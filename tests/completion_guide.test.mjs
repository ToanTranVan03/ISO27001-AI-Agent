import test from 'node:test';
import assert from 'node:assert/strict';
import {buildCompletionGuide} from '../frontend-react/src/completionGuide.js';

function scope(){return {assessment_id:'test',rubric_sha256:'rubric',rubric_approval:null,
 controls:[{control_id:'A.6.1',explicit_source_count:0,usable_source_count:0},
 {control_id:'A.6.2',explicit_source_count:1,usable_source_count:0},
 {control_id:'A.8.1',explicit_source_count:1,usable_source_count:1},
 {control_id:'A.7.1',explicit_source_count:0,applicability:{applicable:false}}],
 acceptance_worklist:{tasks:[{stage:'evaluation',control_id:'A.8.1'},{stage:'review',control_id:'A.8.1'},
 {stage:'applicability',control_id:'A.6.1'},{stage:'treatment',control_id:'A.6.1'}]},
 soa:{fingerprint:'snapshot',pending_controls:['A.6.1'],approval:'DRAFT_NOT_APPROVED'},acceptance:{soa_approved:false}};}

test('guidance separates missing/unusable sources, exclusions and human decisions without mutation',()=>{
 const input=scope(),before=structuredClone(input),g=buildCompletionGuide(input);
 assert.deepEqual(input,before);
 assert.deepEqual(g.steps.find(s=>s.id==='sources').controls,['A.6.1','A.6.2']);
 assert.deepEqual(g.steps.find(s=>s.id==='decisions').controls,['A.6.1']);
 assert.equal(g.steps.find(s=>s.id==='research').pending,null);
 assert.equal(g.steps.find(s=>s.id==='approval').pending,true);
 assert.equal(g.meaning,'GUIDANCE_ONLY_NOT_EVIDENCE_OR_APPROVAL');
});

test('uses current gates rather than claiming compliance from counts',()=>{
 const input=scope();input.rubric_approval={};input.acceptance.soa_approved=true;input.soa.pending_controls=[];
 input.acceptance_worklist.tasks=[];
 const g=buildCompletionGuide(input);
 assert.equal(g.steps.find(s=>s.id==='rubric').pending,false);
 assert.equal(g.steps.find(s=>s.id==='approval').pending,false);
 assert.equal(g.steps.find(s=>s.id==='research').pending,null);
 assert.equal(g.steps.find(s=>s.id==='review').controls.length,0);
});
