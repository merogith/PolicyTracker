import io
import json
import unittest
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from pypdf.generic import DictionaryObject, NameObject, NumberObject, DecodedStreamObject
from policytracker.preparation import page_concerns, read_review, ocr_page
from policytracker.profiles import sha, validate_bundle, demo_bundle
from test_method_customization import workspace_test_directory

ROOT=Path(__file__).resolve().parents[1]


class PreparationTests(unittest.TestCase):
    def test_sparse_blank_rotated_corrupt_and_mixed_pages_are_distinct_signals(self):
        writer=PdfWriter();page=writer.add_blank_page(width=100,height=100)
        self.assertEqual(page_concerns(page,''),['sparse_text'])
        page.rotate(90)
        self.assertIn('rotated_page',page_concerns(page,'Readable words '*30))
        self.assertIn('damaged_text',page_concerns(page,'bad\ufffd words '*30))
        image=DictionaryObject({NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(600),NameObject('/Height'):NumberObject(600)})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Im1'):image})})
        # A shared but unused image resource must not block a text-only page.
        self.assertNotIn('raster_content_may_contain_text',page_concerns(page,'Many readable words '*100))
        stream=DecodedStreamObject();stream.set_data(b'q /Im1 Do Q')
        page[NameObject('/Contents')]=stream
        self.assertIn('raster_content_may_contain_text',page_concerns(page,'Many readable words '*100))
    def test_derived_review_requires_exact_source_page_hash_and_visual_note(self):
        with workspace_test_directory() as root:
            key='a'*64;path=root/'data/derived/reading'/key/'page-2.json';path.parent.mkdir(parents=True)
            item={'source_sha256':key,'page':2,'text':'','text_sha256':sha(b''),'method':'nontext','reviewed':True,'note':'Inspected image: blank separator'}
            path.write_text(json.dumps(item));self.assertEqual(read_review(root,key,2)['method'],'nontext')
            for field,bad in (('reviewed',False),('page',3),('text_sha256','b'*64),('note','')):
                path.write_text(json.dumps({**item,field:bad}))
                with self.assertRaises(ValueError):read_review(root,key,2)
    def test_ocr_missing_engine_has_actionable_error_without_touching_original(self):
        with workspace_test_directory() as root:
            source=root/'original.pdf';source.write_bytes(b'unchanged')
            with self.assertRaisesRegex(ValueError,'Install Poppler'):
                ocr_page(root,source,1,'eng',renderer='missing-renderer-policytracker')
            self.assertEqual(source.read_bytes(),b'unchanged')
    def test_explicit_nontext_page_accounting_does_not_create_fake_evidence(self):
        bundle=demo_bundle(ROOT);source=bundle['sources'][0];source['pages']+=1
        source['page_checks']=[{'page':source['pages'],'concerns':['sparse_text'],'parsed_text_sha256':sha(b''),'review':{'source_sha256':source['sha256'],'page':source['pages'],'method':'nontext','reviewed':True,'text':'','text_sha256':sha(b''),'note':'Inspected blank separator'}}]
        validate_bundle(ROOT,bundle)
        source['page_checks'][0]['review']['page']-=1
        with self.assertRaisesRegex(ValueError,'physical source page'):validate_bundle(ROOT,bundle)
        source['page_checks'][0]['review']['page']+=1
        source['page_checks'][0]['review']['reviewed']=False
        with self.assertRaisesRegex(ValueError,'physical source page'):validate_bundle(ROOT,bundle)


if __name__=='__main__':unittest.main()
