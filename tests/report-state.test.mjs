import test from 'node:test';
import assert from 'node:assert/strict';
import {restoreFocus,createProfileCache} from '../design/prototype/report-state.js';

test('initial rendering with no focused ID does not interrupt history initialization',()=>{
 const body={};let lookups=0;
 const main={ownerDocument:{body,activeElement:body,getElementById(){lookups++;return null;}}};
 assert.doesNotThrow(()=>restoreFocus(main,'',undefined));
 assert.doesNotThrow(()=>restoreFocus(main,undefined,undefined));
 assert.equal(lookups,0);
});

test('rerender restores a surviving control without stealing active focus or failing on removed controls',()=>{
 const body={};const calls=[];const control={focus:options=>calls.push(options)};
 const doc={body,activeElement:body,getElementById:id=>id==='kept'?control:null};
 const main={ownerDocument:doc};
 restoreFocus(main,'kept');assert.deepEqual(calls,[{preventScroll:true}]);
 restoreFocus(main,'removed');assert.equal(calls.length,1);
 doc.activeElement=control;restoreFocus(main,'kept');assert.equal(calls.length,1);
});

test('historical reading, regional selections and subsequent generation keep separate version identities',()=>{
 const cache=createProfileCache(),current={selection:{country:'KAZ',profile_id:'new',revision:2},history:[{id:'old',published:1},{id:'new',published:1}],profile:{id:'new',published:true}};
 cache.set('KAZ',current);
 cache.set('KAZ',{...current,profile:{id:'old',published:true}},'old');
 assert.equal(cache.get('KAZ','old').profile.id,'old');
 assert.equal(cache.get('KAZ').profile.id,'new');
 assert.deepEqual([...cache.values()].map(d=>d.profile.id),['new']);
 cache.set('KAZ',{...current,selection:{...current.selection,profile_id:'newest',revision:3},history:[{id:'old',published:0}],profile:{id:'newest',published:true}});
 assert.equal(cache.get('KAZ','old').profile.id,'old','A completed run must not replace an exact historical read');
 assert.equal(cache.get('KAZ','old').profile.published,false,'History reflects publication changes without editing the stored record');
 assert.equal(cache.get('KAZ','old').selection.revision,3);
 assert.equal(cache.get('KAZ').profile.id,'newest');
 cache.set('KAZ',current);assert.equal(cache.get('KAZ').profile.id,'newest','An earlier selection response cannot overwrite a later completion');
 assert.throws(()=>cache.set('KAZ',current,'missing'),/No other version has been substituted/);
 cache.set('KAZ',{error:'Unavailable'},'missing');
 assert.equal(cache.get('KAZ','missing').error,'Unavailable');
 assert.equal(cache.get('KAZ').profile.id,'newest');
});

test('fresh historical reads retain changed history and publication when selection revision is unchanged',()=>{
 const cache=createProfileCache(),selection={country:'KAZ',profile_id:'selected',revision:1};
 const history=[{id:'selected',state:'checked',published:1},{id:'older',state:'checked',published:1}];
 cache.set('KAZ',{selection,history,profile:{id:'selected',published:true}});
 const refreshed=[{id:'failed-update',state:'failed',published:1},history[0],{...history[1],published:0}];
 cache.set('KAZ',{selection,history:refreshed,profile:{id:'older',published:false}},'older');
 assert.deepEqual(cache.get('KAZ','older').history,refreshed);
 assert.deepEqual(cache.get('KAZ').history,refreshed);
 assert.equal(cache.get('KAZ','older').profile.published,false);
 assert.equal(cache.get('KAZ').profile.id,'selected');
 assert.deepEqual([...cache.values()].map(data=>data.profile.id),['selected']);
});

test('a historical response revealing a newer selection invalidates stale selected content',()=>{
 const cache=createProfileCache();
 cache.set('KAZ',{selection:{profile_id:'selected',revision:1},history:[],profile:{id:'selected'}});
 cache.set('KAZ',{selection:{profile_id:'new-selected',revision:2},history:[],profile:{id:'older'}},'older');
 assert.equal(cache.get('KAZ'),undefined,'The caller must load the newly selected version');
 assert.deepEqual([...cache.values()],[],'Regional summaries must not use a superseded selection');
 assert.equal(cache.get('KAZ','older').profile.id,'older');
 cache.set('KAZ',{selection:{profile_id:'new-selected',revision:2},history:[],profile:{id:'new-selected'}});
 assert.equal(cache.get('KAZ').profile.id,'new-selected');
});
