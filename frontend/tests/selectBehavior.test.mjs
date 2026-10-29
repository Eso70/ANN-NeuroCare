import assert from 'node:assert/strict'
import test from 'node:test'
import { listboxPosition, matchingOption, optionIndex } from '../src/lib/selectBehavior.ts'

test('custom select keyboard navigation respects both ends of the list', () => {
  assert.equal(optionIndex(0, 'ArrowUp', 5), 0)
  assert.equal(optionIndex(4, 'ArrowDown', 5), 4)
  assert.equal(optionIndex(0, 'ArrowDown', 5), 1)
  assert.equal(optionIndex(2, 'Home', 5), 0)
  assert.equal(optionIndex(2, 'End', 5), 4)
  assert.equal(optionIndex(2, 'PageDown', 13), 7)
  assert.equal(optionIndex(2, 'PageUp', 13), 0)
  assert.equal(optionIndex(0, 'ArrowDown', 0), -1)
})

test('typeahead matches prefixes and cycles repeated characters', () => {
  const options = ['Never attended', 'High school', 'College 1–3 years', 'College 4+ years']
  assert.equal(matchingOption(options, 'h', -1), 1)
  assert.equal(matchingOption(options, 'col', 2), 2)
  assert.equal(matchingOption(options, 'cc', 2), 3)
  assert.equal(matchingOption(options, 'ccc', 3), 2)
  assert.equal(matchingOption(options, 'unmatched', 1), 1)
})

test('numeric typeahead accepts Arabic and Persian keyboard digits without changing source values', () => {
  const options = ['18-24', '50-54', '55-59', '80 or older']
  assert.equal(matchingOption(options, '5', -1), 1)
  assert.equal(matchingOption(options, '\u0665', -1), 1)
  assert.equal(matchingOption(options, '\u06f5', -1), 1)
  assert.equal(matchingOption(options, '\u0665\u0665', 1), 2)
  assert.equal(matchingOption(options, '\u06f8\u06f0', -1), 3)
})

test('dropdowns fit narrow viewports and open above a trigger near the bottom', () => {
  const viewport = { width: 320, height: 640 }
  const rect = { left: 240, top: 580, bottom: 636, width: 300 }
  const popup = listboxPosition(rect, viewport, 13)
  assert.ok(popup.left >= 12)
  assert.ok(popup.left + popup.width <= viewport.width - 12)
  assert.ok(popup.top >= 12)
  assert.ok(popup.top + popup.maxHeight <= rect.top - 8)
})

test('a trigger near the top opens downwards with room to scroll', () => {
  const popup = listboxPosition({ left: 20, top: 20, bottom: 76, width: 280 }, { width: 400, height: 858 }, 13)
  assert.equal(popup.top, 84)
  assert.equal(popup.width, 280)
  assert.equal(popup.maxHeight, 300)
})
