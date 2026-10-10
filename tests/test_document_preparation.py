"""Document recovery tests use local invented PDFs and fake OCR, never a model."""
import http.client
import io
import json
import subprocess
import threading
import unittest
from unittest.mock import Mock, patch

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject

from policytracker.ai_runtime import AIError
from policytracker.country_runs import CountryRunner
from policytracker.local_server import LocalServer
from policytracker.preparation import (PreparationRequired, extract_page, inspect_document,
    ocr_page, page_concerns, parsed_pages, read_review, recover_page, review_path, run_local, save_review, validate_review)
from policytracker.profiles import sha
from test_method_customization import workspace_test_directory


def pdf_bytes(width=100):
    writer = PdfWriter()
    writer.add_blank_page(width=width, height=100)
    buffer = io.BytesIO(); writer.write(buffer)
    return buffer.getvalue()


class DocumentPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = workspace_test_directory()
        self.root = self.temp.__enter__()
        parsed_pages.cache_clear()
        self.service = Mock()
        self.runner = CountryRunner(self.root, self.root / 'store.sqlite3', self.service)
        self.docs = []

    def tearDown(self):
        parsed_pages.cache_clear()
        self.temp.__exit__(None, None, None)

    def document(self, name='doc-one', raw=None):
        raw = pdf_bytes() if raw is None else raw
        path = self.root / 'data/sources/Kazakhstan/NDC' / name / 'Current.pdf'
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        doc = dict(document_id=name, title=name, country_code='KAZ', relative_path=path.relative_to(self.root).as_posix(), sha256=sha(raw))
        self.docs.append(doc)
        manifest = self.root / 'data/manifests/corpus.json'; manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({'documents': self.docs}), encoding='utf-8')
        with self.runner.store() as store: store.put(raw)
        return doc

    def receipt(self, doc, text='Checked source text with all table cells and chart labels.'):
        return dict(source_sha256=doc['sha256'], page=1, method='reviewed_text', text=text,
                    text_sha256=sha(text.encode()), reviewed=True, note='Compared every word with the original.')

    def test_all_documents_and_broken_files_are_reported_before_any_model_call(self):
        self.document('doc-a'); self.document('doc-b', pdf_bytes(110)); self.document('doc-broken', b'broken PDF')
        report = self.runner.preparation({'action':'inspect', 'country':'KAZ', 'document_ids':[d['document_id'] for d in self.docs]})
        self.assertFalse(report['ready']); self.assertEqual(report['pages_needing_review'], 2)
        self.assertIn('Cannot open this PDF', report['documents'][-1]['error'])
        with self.assertRaises(PreparationRequired) as error:
            self.runner.prepare_sources({'country':'KAZ', 'documents':self.docs})
        self.assertEqual(len(error.exception.documents), 3)
        self.service.generate_json.assert_not_called()

    def test_parse_failure_is_recoverable_by_review_and_keeps_source_fingerprint(self):
        doc = self.document()
        page = Mock(extract_text=Mock(side_effect=ValueError('Broken font')))
        text, flags = extract_page(page)
        self.assertEqual(text, ''); self.assertEqual(flags, ['parse_failed:ValueError'])
        with patch('policytracker.preparation.parsed_pages', return_value=((text, tuple(flags)),)):
            self.assertTrue(inspect_document(self.root, doc)[0]['needs_review'])
            save_review(self.root, self.receipt(doc))
            source = self.runner.prepare_sources({'country':'KAZ','documents':[doc]})[0]
        self.assertEqual(source['sha256'], doc['sha256'])
        self.assertEqual(source['segments'][0]['text'], self.receipt(doc)['text'])
        self.assertEqual(source['page_checks'][0]['concerns'], flags)

    def test_parse_cache_reuses_only_exact_bytes_and_always_rereads_reviews(self):
        doc = self.document()
        with patch('pypdf.PdfReader', wraps=PdfReader) as reader:
            self.assertTrue(inspect_document(self.root, doc)[0]['needs_review'])
            save_review(self.root, self.receipt(doc))
            self.assertFalse(inspect_document(self.root, doc)[0]['needs_review'])
            self.assertEqual(reader.call_count, 1)
            parsed_pages(pdf_bytes(120)); self.assertEqual(reader.call_count, 2)

    def test_saved_review_cannot_be_overwritten_or_silently_accept_changed_text(self):
        doc = self.document(); item = self.receipt(doc); target = save_review(self.root, item)
        original = target.read_bytes()
        with self.assertRaisesRegex(ValueError, 'already exists'): save_review(self.root, self.receipt(doc, 'Different text'))
        self.assertEqual(target.read_bytes(), original)
        changed = {**item, 'text':'Changed without hash'}; target.write_text(json.dumps(changed))
        report = self.runner.preparation({'action':'inspect','country':'KAZ','document_ids':[doc['document_id']]})
        self.assertFalse(report['ready']); self.assertIn('hash differs', report['documents'][0]['pages'][0]['review_error'])

    def test_save_requires_confirmation_current_source_no_active_job_and_nonempty_text(self):
        doc = self.document()
        payload = dict(action='save', document_id=doc['document_id'], page=1, source_sha256=doc['sha256'],
                       method='reviewed_text', text='Complete checked text', note='Checked original.', confirmed=True)
        for key, bad in [('confirmed',False),('source_sha256','f'*64),('text',''),('note',''),('method','automatic')]:
            with self.subTest(key=key), self.assertRaises(AIError): self.runner.preparation({**payload,key:bad})
        self.runner.active = 'running'
        with self.assertRaisesRegex(AIError,'Stop the active'): self.runner.preparation(payload)
        self.runner.active = None
        self.assertTrue(self.runner.preparation(payload)['saved'])
        with self.assertRaisesRegex(AIError,'already has a saved review'): self.runner.preparation(payload)
        self.assertTrue(self.runner.preparation({'action':'inspect','country':'KAZ','document_ids':[doc['document_id']]})['ready'])
        self.service.generate_json.assert_not_called()

    def test_invalid_page_changed_source_and_unregistered_source_are_rejected(self):
        doc = self.document()
        for number in (0, 2, True, '1'):
            with self.assertRaises(AIError): self.runner.preparation({'action':'page','document_id':doc['document_id'],'page':number})
        with self.assertRaises(AIError): self.runner.preparation({'action':'page','document_id':'../../private','page':1})
        (self.root / doc['relative_path']).write_bytes(pdf_bytes(130))
        with self.assertRaisesRegex(AIError,'differs from inventory'):
            self.runner.preparation({'action':'page','document_id':doc['document_id'],'page':1})

    def test_legacy_review_failure_cannot_launch_another_futile_resume(self):
        job = dict(id='old-run',country='KAZ',status='failed',stage='prepare',error='Page 15: text needs inspection')
        with self.runner.store() as store: self.runner.write(store, job)
        public = self.runner.status('KAZ')['runs'][0]
        self.assertFalse(public['can_resume']); self.assertEqual(public['required_action'],'review_sources')
        session = Mock(lock=threading.RLock())
        with self.assertRaisesRegex(AIError,'start a new run'): self.runner.resume(session,'old-run')
        self.assertEqual(self.runner.get('old-run')['error'], job['error'])

    def test_nontext_review_accounts_for_blank_but_does_not_make_empty_document_ready(self):
        doc = self.document(); item = {**self.receipt(doc,''),'method':'nontext'}
        save_review(self.root,item)
        report = self.runner.inspect_sources([doc])
        self.assertFalse(report['ready']); self.assertIn('No substantive text',report['documents'][0]['error'])

    def test_corrupt_draft_is_reported_and_cannot_crash_or_be_silently_approved(self):
        doc = self.document()
        candidate = review_path(self.root, doc['sha256'], 1, candidate=True)
        candidate.parent.mkdir(parents=True); candidate.write_text('[]', encoding='utf-8')
        page = self.runner.preparation(dict(action='page', document_id=doc['document_id'], page=1))
        self.assertIsNone(page['candidate']); self.assertTrue(page['candidate_error'])
        with self.assertRaises(AIError):
            self.runner.preparation(dict(action='save', document_id=doc['document_id'], page=1,
                source_sha256=doc['sha256'], method='reviewed_text', text='Checked transcription',
                note='Inspected original', confirmed=True))
        self.assertEqual(candidate.read_text(), '[]')
        self.assertIsNone(read_review(self.root, doc['sha256'], 1))

    def test_password_protected_pdf_is_an_actionable_document_error(self):
        writer=PdfWriter();writer.add_blank_page(width=100,height=100);writer.encrypt('secret')
        buffer=io.BytesIO();writer.write(buffer)
        doc=self.document(raw=buffer.getvalue())
        report=self.runner.inspect_sources([doc])
        self.assertIn('password protected',report['documents'][0]['error'])

    def test_nested_used_image_is_detected_but_unused_resources_are_not(self):
        writer=PdfWriter();page=writer.add_blank_page(width=100,height=100)
        image=DictionaryObject({NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(600),NameObject('/Height'):NumberObject(600)})
        form=DecodedStreamObject();form.set_data(b'/Im Do');form[NameObject('/Subtype')]=NameObject('/Form')
        form[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Im'):image})})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Form1'):form})})
        self.assertNotIn('raster_content_may_contain_text',page_concerns(page,'Readable text '*10))
        content=DecodedStreamObject();content.set_data(b'/Form1 Do');page[NameObject('/Contents')]=content
        self.assertIn('raster_content_may_contain_text',page_concerns(page,'Readable text '*10))

    def test_painted_tables_and_charts_need_recovery_even_with_readable_prose(self):
        writer=PdfWriter(); page=writer.add_blank_page(width=600,height=800)
        table=b' '.join(f'50 {y} m 550 {y} l'.encode() for y in range(100,500,40))
        stream=DecodedStreamObject(); page[NameObject('/Contents')]=stream
        # A real chart grid/table is significant; a clipping path with the same
        # geometry and a small decorative grid must not add inference requests.
        for content, expected in [(table+b' S', True), (table+b' W n', False),
                                  (b'q .01 0 0 .01 0 0 cm '+table+b' S Q', False),
                                  (b'50 50 500 700 re S', False),
                                  (b' '.join(f'50 {y} 500 20 re f'.encode() for y in range(100,500,40)), False),
                                  (b' '.join(f'50 {y} 500 1 re f'.encode() for y in range(100,260,40)), False),
                                  (b' '.join(f'50 {y} 500 1 re f'.encode() for y in range(100,500,40)), True)]:
            with self.subTest(content=content):
                stream.set_data(content)
                self.assertEqual('vector_content_may_convey_structure' in page_concerns(page,'Readable prose '*20), expected)

    def test_vector_detection_follows_used_forms_and_their_display_transform(self):
        writer=PdfWriter(); page=writer.add_blank_page(width=600,height=800)
        form=DecodedStreamObject(); form[NameObject('/Subtype')]=NameObject('/Form')
        form.set_data(b' '.join(f'0 {y/10} m 1 {y/10} l'.encode() for y in range(10))+b' S')
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Chart'):form})})
        self.assertNotIn('vector_content_may_convey_structure',page_concerns(page,'Readable prose '*20))
        content=DecodedStreamObject(); content.set_data(b'q 400 0 0 400 50 100 cm /Chart Do Q')
        page[NameObject('/Contents')]=content
        self.assertIn('vector_content_may_convey_structure',page_concerns(page,'Readable prose '*20))

    def test_alternate_text_alone_cannot_certify_a_vector_table(self):
        doc=self.document()
        page=dict(page=1,text='Costs 2025 2026 100 200',concerns=['vector_content_may_convey_structure'],review=None)
        with patch('policytracker.preparation.alternate_text',return_value='Costs 2025 2026 100 200'), patch('policytracker.preparation.find_ocr_engine',return_value=None):
            result=recover_page(self.root,doc,page,{'vision_recovery':False})
        self.assertEqual(result['status'],'partial')
        self.assertEqual(result['text'],page['text'])
        self.assertTrue(result['notes'])

    def test_rotated_table_and_failed_graphics_inspection_keep_partial_coverage(self):
        doc=self.document()
        writer=PdfWriter(); pdf_page=writer.add_blank_page(width=600,height=800); pdf_page.rotate(90)
        content=DecodedStreamObject(); content.set_data(b' '.join(f'50 {y} m 550 {y} l'.encode() for y in range(100,500,40))+b' S')
        pdf_page[NameObject('/Contents')]=content
        text='Costs in 2025 and 2026 are 100 and 200.'
        # Rotation already routes whole-page recovery, so the extra vector walk
        # is skipped. Its absence must not let alternate text certify the table.
        cases=[page_concerns(pdf_page,text), ['inspection_failed:ValueError'], ['parse_failed:ValueError']]
        self.assertEqual(cases[0], ['rotated_page'])
        for concerns in cases:
            with self.subTest(concerns=concerns), patch('policytracker.preparation.alternate_text',return_value=text), patch('policytracker.preparation.find_ocr_engine',return_value=None):
                result=recover_page(self.root,doc,dict(page=1,text=text,concerns=concerns,review=None),{'vision_recovery':False})
            self.assertEqual(result['status'],'partial')
            self.assertEqual(result['text'],text)

    def test_automatic_ocr_does_not_silently_exclude_later_installed_languages(self):
        doc=self.document()
        page=dict(page=1,text='',concerns=['sparse_text'],review=None)
        candidate=dict(text='Recovered words',review_image='page.png',render_sha256='a'*64,ocr_tsv='page.tsv',tsv_sha256='b'*64)
        with patch('policytracker.preparation.alternate_text',return_value=''), patch('policytracker.preparation.find_ocr_engine',return_value='tesseract'), patch('policytracker.preparation.run_local',return_value=Mock(stdout=b'List of available languages (7):\ndeu\neng\nfra\nita\nosd\nrus\ntur\n')), patch('policytracker.preparation.ocr_page',return_value=candidate) as ocr:
            result=recover_page(self.root,doc,page,{'vision_recovery':False,'ocr_languages':'auto'})
        self.assertEqual(ocr.call_args.args[3],'deu+eng+fra+ita+rus+tur')
        self.assertEqual(result['status'],'partial')

    def test_ocr_keeps_unapproved_word_data_and_validates_artifact_integrity(self):
        doc=self.document(); source=self.root/doc['relative_path']
        folder=review_path(self.root,doc['sha256'],1).parent/'ocr-test';folder.mkdir(parents=True)
        image=folder/'page.png';image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
        tsv=b'block_num\tpar_num\tline_num\tconf\ttext\n1\t1\t1\t95\tFlood\n1\t1\t1\t70\t2030\n'
        def command(args,*unused):
            return Mock(stdout=b'List of available languages (1):\neng\n' if '--list-langs' in args else b'tesseract fixture\n' if '--version' in args else tsv)
        with patch('policytracker.preparation.shutil.which',return_value='available'), patch('policytracker.preparation.render_page',return_value=image), patch('policytracker.preparation.run_local',side_effect=command):
            item=ocr_page(self.root,source,1,'eng')
        self.assertFalse(item['reviewed']);self.assertEqual(item['text'],'Flood 2030');self.assertEqual(item['ocr_low_confidence_words'],1)
        save_review(self.root,item,candidate=True)
        self.assertIsNone(read_review(self.root,doc['sha256'],1))
        approved={**item,'reviewed':True,'note':'Compared the number and text with original.'}
        validate_review(self.root,approved,doc['sha256'],1)
        save_review(self.root,approved)
        frozen=self.runner.page_reviews([doc])
        self.assertIn(item['review_image'],frozen);self.assertIn(item['ocr_tsv'],frozen)
        image.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'artifact hash differs'):save_review(self.root,approved)
        with self.assertRaisesRegex(ValueError,'artifact hash differs'):self.runner.page_reviews([doc])

    def test_missing_ocr_language_and_timeout_are_actionable_and_do_not_approve(self):
        doc=self.document()
        with patch('policytracker.preparation.shutil.which',return_value='available'), patch('policytracker.preparation.run_local',return_value=Mock(stdout=b'eng\n')):
            with self.assertRaisesRegex(ValueError,'Missing installed OCR language packs: rus'):
                ocr_page(self.root,self.root/doc['relative_path'],1,'rus')
        with patch('policytracker.preparation.subprocess.run',side_effect=subprocess.TimeoutExpired('fake',1)):
            with self.assertRaisesRegex(ValueError,'OCR timed out'):run_local(['fake'],'OCR',1)
        self.assertIsNone(read_review(self.root,doc['sha256'],1))

    def test_preparation_http_requires_session_origin_csrf_and_never_calls_model(self):
        doc=self.document()
        server=LocalServer(self.root,port=0,service=self.service,profiles_path=self.root/'store.sqlite3')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
        try:
            payload=json.dumps({'action':'inspect','country':'KAZ','document_ids':[doc['document_id']]})
            conn.request('POST','/api/ai/preparation',payload,{'Content-Type':'application/json'})
            response=conn.getresponse();self.assertEqual(response.status,401);response.read()
            conn.request('GET','/api/ai/session');response=conn.getresponse();cookie=response.getheader('Set-Cookie').split(';')[0];token=json.loads(response.read())['csrf']
            headers={'Cookie':cookie,'Content-Type':'application/json','X-PolicyTracker-CSRF':token}
            for extra in [{'X-PolicyTracker-CSRF':'wrong'},{'Origin':'https://other.example'}]:
                conn.request('POST','/api/ai/preparation',payload,{**headers,**extra})
                response=conn.getresponse();self.assertEqual(response.status,403);response.read()
            conn.request('POST','/api/ai/preparation',payload,headers);response=conn.getresponse()
            self.assertEqual(response.status,200);self.assertFalse(json.loads(response.read())['ready'])
            conn.request('GET','/api/ai/preparation/doc-one/1/render');response=conn.getresponse()
            self.assertEqual(response.status,401);response.read()
            conn.request('POST','/api/ai/preparation',json.dumps({'action':'page','document_id':'unknown','page':1}),headers)
            response=conn.getresponse();self.assertEqual(response.status,400);self.assertIn('Selected documents',json.loads(response.read())['error']['message'])
            self.service.generate_json.assert_not_called()
        finally:
            conn.close();server.shutdown();server.server_close();thread.join(5)


if __name__=='__main__':unittest.main()
