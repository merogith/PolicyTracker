import test from 'node:test';
import assert from 'node:assert/strict';
import {editedFileContent} from '../design/prototype/knowledge-view.js';

test('restoring visible text preserves exact CRLF and mixed source fingerprints',()=>{
 for(const original of ['# Prompt\r\nKeep evidence.\r\n','# Prompt\nKeep evidence.\n','# Prompt\r\nMixed ending.\n']){
  assert.equal(editedFileContent(original,original.replaceAll('\r\n','\n')),original);
 }
});

test('an intentional edit keeps the existing consistent line-ending convention',()=>{
 assert.equal(editedFileContent('First\r\nSecond\r\n','First\nRevised\n'),'First\r\nRevised\r\n');
 assert.equal(editedFileContent('First\nSecond\n','First\nRevised\n'),'First\nRevised\n');
});
