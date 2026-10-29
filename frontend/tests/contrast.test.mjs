import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const css = ['tokens.css','site.css','forms.css'].map(name => readFileSync(new URL(`../src/styles/${name}`, import.meta.url), 'utf8')).join('\n')
const token = name => css.match(new RegExp(`--${name}:\\s*(#[0-9a-f]{6})`, 'i'))[1]

function color(selector) {
  const start = css.indexOf(`${selector} {`)
  assert.ok(start >= 0, `Missing style for ${selector}`)
  const declaration = css.slice(start, css.indexOf('}', start)).match(/(?:^|[;{])\s*color:\s*([^;]+)/)[1]
  const variable = declaration.match(/^var\(--([\w-]+)\)$/)
  return variable ? token(variable[1]) : declaration
}

function luminance(hex) {
  const channels = [1, 3, 5].map(offset => parseInt(hex.slice(offset, offset + 2), 16) / 255)
    .map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4)
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722
}

test('shared control text and supporting copy meet 4.5:1 on their actual backgrounds', () => {
  for (const [selector, background] of [
    ['.eyebrow', token('paper')],
    ['.field-hint', token('white')],
    ['.field-label', token('white')],
    ['.required-mark', token('white')],
    ['.field-error', token('white')],
    ['.button--primary', token('ink')],
  ]) {
    const [dark, light] = [luminance(color(selector)), luminance(background)].sort((a, b) => a - b)
    const contrast = (light + 0.05) / (dark + 0.05)
    assert.ok(contrast >= 4.5, `${selector}: ${contrast.toFixed(2)}:1`)
  }
})

test('lavender surfaces and accent controls retain readable contrast', () => {
  for (const [foreground, background] of [
    [token('muted'), token('lavender')],
    [token('accent'), token('paper')],
    [token('white'), token('accent')],
    [token('lavender'), token('deep')],
  ]) {
    const [dark, light] = [luminance(foreground), luminance(background)].sort((a, b) => a - b)
    assert.ok((light + 0.05) / (dark + 0.05) >= 4.5)
  }
})
