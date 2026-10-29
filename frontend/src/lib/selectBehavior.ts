export function optionIndex(current: number, key: string, count: number): number {
  if (!count) return -1
  if (key === 'Home') return 0
  if (key === 'End') return count - 1
  const delta = key === 'ArrowDown' ? 1 : key === 'ArrowUp' ? -1 : key === 'PageDown' ? 5 : key === 'PageUp' ? -5 : 0
  return Math.max(0, Math.min(count - 1, current + delta))
}

function searchText(value: string): string {
  return value.toLocaleLowerCase()
    .replace(/[\u0660-\u0669]/g, digit => String(digit.charCodeAt(0) - 0x0660))
    .replace(/[\u06f0-\u06f9]/g, digit => String(digit.charCodeAt(0) - 0x06f0))
}

export function matchingOption(labels: string[], query: string, current: number): number {
  const normalized = searchText(query)
  const repeated = [...normalized].every(character => character === normalized[0])
  const prefix = repeated ? normalized[0] : normalized
  const start = repeated ? current + 1 : current
  for (let offset = 0; offset < labels.length; offset++) {
    const index = (Math.max(0, start) + offset) % labels.length
    if (searchText(labels[index]).startsWith(prefix)) return index
  }
  return current
}

export function listboxPosition(rect: { left: number; top: number; bottom: number; width: number }, viewport: { width: number; height: number }, count: number) {
  const margin = 12, gap = 8
  const width = Math.min(rect.width, Math.max(1, viewport.width - margin * 2))
  const below = Math.max(0, viewport.height - rect.bottom - gap - margin)
  const above = Math.max(0, rect.top - gap - margin)
  const placeBelow = below >= Math.min(240, count * 48 + 12) || below >= above
  const maxHeight = Math.min(300, placeBelow ? below : above)
  const height = Math.min(count * 48 + 12, maxHeight)
  return { left: Math.max(margin, Math.min(rect.left, viewport.width - width - margin)),
    top: Math.max(margin, placeBelow ? rect.bottom + gap : rect.top - gap - height), width, maxHeight }
}
