import assert from 'node:assert/strict'
import test from 'node:test'
import { apiBaseUrl } from '../src/lib/apiOrigin.ts'

test('production without an API override uses the page origin', () => {
  assert.equal(apiBaseUrl(undefined), '')
  assert.equal(apiBaseUrl(''), '')
  assert.equal(apiBaseUrl('   '), '')
})

test('local development keeps the existing API default', () => {
  assert.equal(apiBaseUrl(undefined, 'http://localhost:8000'), 'http://localhost:8000')
})

test('an explicit API deployment URL wins in either mode', () => {
  for (const fallback of ['http://localhost:8000', '']) {
    assert.equal(apiBaseUrl('  https://api.example.test  ', fallback), 'https://api.example.test')
    assert.equal(apiBaseUrl('/backend', fallback), '/backend')
  }
})
