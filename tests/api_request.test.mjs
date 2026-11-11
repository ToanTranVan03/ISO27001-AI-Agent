import test from 'node:test';
import assert from 'node:assert/strict';
import {apiRequest,ApiError} from '../frontend-react/src/api.js';

test('authenticated JSON requests preserve the API contract',async t=>{
  t.mock.method(globalThis,'fetch',async(path,options)=>{
    assert.equal(path,'/api/test');
    assert.equal(options.headers.get('Authorization'),'Bearer test-token');
    assert.equal(options.headers.get('Content-Type'),'application/json');
    return new Response(JSON.stringify({saved:true}),{status:200});
  });
  assert.deepEqual(await apiRequest('/api/test','test-token',{method:'POST',body:JSON.stringify({a:1})}),{saved:true});
});

test('document uploads leave multipart boundary generation to the browser',async t=>{
  const body=new FormData();body.append('evidence_type','document');
  t.mock.method(globalThis,'fetch',async(_path,options)=>{
    assert.equal(options.body,body);
    assert.equal(options.headers.has('Content-Type'),false);
    return new Response('{}',{status:201});
  });
  await apiRequest('/upload','token',{method:'POST',body});
});

test('expired sessions expose 401 for the app to clear authentication',async t=>{
  t.mock.method(globalThis,'fetch',async()=>new Response(JSON.stringify({detail:'Session expired'}),{status:401}));
  await assert.rejects(apiRequest('/private','token'),e=>e instanceof ApiError&&e.status===401&&e.message==='Session expired');
});

test('structured validation failures remain API errors',async t=>{
  t.mock.method(globalThis,'fetch',async()=>new Response(JSON.stringify({detail:[{msg:'Invalid input'}]}),{status:422}));
  await assert.rejects(apiRequest('/validate'),e=>e instanceof ApiError&&e.status===422);
});

test('network failures are distinguishable from server rejection',async t=>{
  t.mock.method(globalThis,'fetch',async()=>{throw new TypeError('offline');});
  await assert.rejects(apiRequest('/private'),e=>e instanceof ApiError&&e.status===0);
});
