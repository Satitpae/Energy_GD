import test from 'node:test';import assert from 'node:assert/strict';
import {senderStatusView} from '../dashboard/sender-status.mjs';
test('status uses server time and becomes stale without another browser request',()=>{
 const s={last_seen_at:'2026-10-26T12:00:00Z',server_time:'2026-10-26T12:01:00Z',stale_after_seconds:180};
 assert.equal(senderStatusView(s,0).state,'connected');
 assert.equal(senderStatusView(s,121).state,'stale');
 assert.match(senderStatusView(s,0).timestamp,/19:00:00/);
});
test('unknown and unavailable states never imply a live sender',()=>{
 assert.equal(senderStatusView({last_seen_at:null,server_time:'2026-10-26T12:00:00Z'}).state,'unknown');
 assert.equal(senderStatusView(null).state,'unavailable');
 assert.equal(senderStatusView({last_seen_at:'bad',server_time:'bad'}).state,'unavailable');
});
