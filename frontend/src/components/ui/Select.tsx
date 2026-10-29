import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { Check, ChevronDown } from 'lucide-react'
import { listboxPosition, matchingOption, optionIndex } from '../../lib/selectBehavior'

type Props = {
  name: string; value: string; options: { value: number; label: string }[]; onChange: (value: string) => void
  disabled?: boolean; invalid?: boolean; describedBy?: string; placeholder?: string
}

/** Browser popover handles top-layer placement/dismissal; focus stays on the ARIA combobox. */
export const Select = forwardRef<HTMLButtonElement, Props>(function Select({ name, value, options, onChange, disabled, invalid, describedBy, placeholder = 'Choose an answer' }, ref) {
  const trigger = useRef<HTMLButtonElement>(null)
  const panel = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const [position, setPosition] = useState<ReturnType<typeof listboxPosition>>()
  const search = useRef({ text: '', time: 0 })
  const anchor = useRef<{ top: number; left: number } | null>(null)
  const nativePopover = typeof HTMLElement !== 'undefined' && 'showPopover' in HTMLElement.prototype
  const selected = options.findIndex(option => String(option.value) === value)
  const panelId = `${name}-options`
  useImperativeHandle(ref, () => trigger.current!, [])

  function reposition() {
    if (!trigger.current) return
    const rect = trigger.current.getBoundingClientRect()
    anchor.current = { top: rect.top, left: rect.left }
    setPosition(listboxPosition(rect, { width: window.innerWidth, height: window.innerHeight }, options.length))
  }
  const close = useCallback(() => {
    if (nativePopover && panel.current?.matches(':popover-open')) panel.current.hidePopover()
    setOpen(false)
    search.current = { text: '', time: 0 }
  }, [nativePopover])
  function show(index = selected >= 0 ? selected : 0) {
    if (disabled || !options.length) return
    reposition(); setActive(index); setOpen(true)
    if (nativePopover && !panel.current?.matches(':popover-open')) panel.current?.showPopover()
  }
  function commit(index: number, restoreFocus = true) {
    const option = options[index]
    if (option) onChange(String(option.value))
    close()
    if (restoreFocus) trigger.current?.focus()
  }
  useEffect(() => {
    const element = panel.current
    if (!element || !nativePopover) return
    const toggled = (event: Event) => setOpen((event as ToggleEvent).newState === 'open')
    element.addEventListener('toggle', toggled)
    return () => element.removeEventListener('toggle', toggled)
  }, [nativePopover])
  useEffect(() => {
    if (!open) return
    const list = panel.current
    const option = document.getElementById(`${name}-option-${active}`)
    if (!list || !option) return
    // Scroll only the options, never the page containing the focused trigger.
    if (option.offsetTop < list.scrollTop + 6) list.scrollTop = option.offsetTop - 6
    else if (option.offsetTop + option.offsetHeight > list.scrollTop + list.clientHeight - 6) {
      list.scrollTop = option.offsetTop + option.offsetHeight - list.clientHeight + 6
    }
  }, [active, name, open])
  useEffect(() => {
    if (!open) return
    const dismiss = (event: PointerEvent) => {
      if (!trigger.current?.contains(event.target as Node) && !panel.current?.contains(event.target as Node)) close()
    }
    // Closing on viewport movement avoids an orphaned floating panel on mobile/zoom.
    const moved = (event: Event) => {
      if (event.target === panel.current || panel.current?.contains(event.target as Node)) return
      const rect = trigger.current?.getBoundingClientRect()
      // Ignore a queued focus-scroll event when the trigger has not moved since opening.
      if (!rect || !anchor.current || Math.abs(rect.top - anchor.current.top) > 1 || Math.abs(rect.left - anchor.current.left) > 1) close()
    }
    document.addEventListener('pointerdown', dismiss)
    window.addEventListener('resize', close)
    document.addEventListener('scroll', moved, true)
    return () => {
      document.removeEventListener('pointerdown', dismiss)
      window.removeEventListener('resize', close)
      document.removeEventListener('scroll', moved, true)
    }
  }, [open, close])

  function keyboard(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === 'Escape') { if (open) { event.preventDefault(); event.stopPropagation(); close() }; return }
    if (event.key === 'Tab') { if (open) commit(active, false); return }
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      if (open) commit(active); else show()
      return
    }
    if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'PageUp', 'PageDown'].includes(event.key)) {
      event.preventDefault()
      if (!open) show(event.key === 'End' ? options.length - 1 : event.key === 'Home' ? 0 : selected >= 0 ? selected : 0)
      else setActive(index => optionIndex(index, event.key, options.length))
      return
    }
    if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault()
      const now = Date.now()
      search.current = { text: now - search.current.time > 700 ? event.key : search.current.text + event.key, time: now }
      const index = matchingOption(options.map(option => option.label), search.current.text, open ? active : selected)
      if (!open) show(index < 0 ? 0 : index); else setActive(index)
    }
  }
  return <div className="select-control">
    <button ref={trigger} id={name} type="button" className="select-trigger" role="combobox" aria-required="true"
      aria-labelledby={`${name}-label ${name}-value`} aria-describedby={describedBy} aria-expanded={open}
      aria-controls={panelId} aria-haspopup="listbox" aria-activedescendant={open ? `${name}-option-${active}` : undefined}
      aria-invalid={invalid} disabled={disabled} data-placeholder={selected < 0 || undefined}
      onKeyDown={keyboard} onClick={() => open ? close() : show()}>
      <span id={`${name}-value`}>{selected < 0 ? placeholder : options[selected].label}</span><ChevronDown size={18} aria-hidden="true" />
    </button>
    <div ref={panel} id={panelId} className="select-panel" role="listbox" aria-labelledby={`${name}-label`}
      popover={nativePopover ? 'auto' : undefined} hidden={!nativePopover && !open} style={position}>
      {options.map((option, index) => <div key={option.value} id={`${name}-option-${index}`} role="option"
        className="select-option" aria-selected={String(option.value) === value} data-active={active === index}
        onPointerMove={event => { if (event.pointerType === 'mouse') setActive(index) }}
        onPointerDown={event => { if (event.pointerType === 'mouse') event.preventDefault() }} onClick={() => commit(index)}>
        <span>{option.label}</span>{String(option.value) === value && <Check size={16} aria-hidden="true" />}
      </div>)}
    </div>
  </div>
})
