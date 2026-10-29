/** Offline visual QA only. Does not modify the app or simulate a successful prediction.
 * Input: .dev-logs/design-review/project-data.json exported from public backend readers.
 * Build the frontend first so the review uses its actual compiled CSS.
 */
import { readFile, writeFile, readdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const directory = resolve(root, '.dev-logs/design-review')
const snapshot = JSON.parse(await readFile(resolve(directory, 'project-data.json'), 'utf8'))
const entry = `
import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AxiosError, CanceledError } from 'axios';
import { AppLayout } from '../../frontend/src/layouts/AppLayout';
import { Dashboard } from '../../frontend/src/pages/Dashboard';
import { Prediction } from '../../frontend/src/pages/Prediction';
import { ModelPage } from '../../frontend/src/pages/ModelPage';
import { About } from '../../frontend/src/pages/About';
import { NotFound } from '../../frontend/src/pages/NotFound';
import { api } from '../../frontend/src/services/api';
const saved = ${JSON.stringify(snapshot)};
api.defaults.adapter = async config => {
  if (config.signal?.aborted) throw new CanceledError();
  if (config.method === 'get' && ['/api/v1/model','/api/v1/model/contract'].includes(config.url)) {
    return {data: config.url.endsWith('/contract') ? saved.contract : saved.model, status:200, statusText:'Saved project metadata', headers:{}, config};
  }
  throw new AxiosError('Offline design review: live requests and prediction writes are disabled.', 'ERR_NETWORK', config);
};
createRoot(document.getElementById('review-root')).render(<MemoryRouter><Routes><Route element={<AppLayout />}><Route index element={<Dashboard />} /><Route path='predictions' element={<Prediction />} /><Route path='model' element={<ModelPage />} /><Route path='about' element={<About />} /><Route path='*' element={<NotFound />} /></Route></Routes></MemoryRouter>);
`
const entryPath = resolve(directory, 'entry.tsx')
await writeFile(entryPath, entry)
const { build } = await import(pathToFileURL(resolve(root, 'frontend/node_modules/esbuild/lib/main.js')).href)
const result = await build({
  entryPoints: [entryPath], absWorkingDir: resolve(root, 'frontend'), bundle: true,
  write: false, format: 'iife', platform: 'browser', jsx: 'automatic', minify: true,
  nodePaths: [resolve(root, 'frontend/node_modules')],
  define: { 'process.env.NODE_ENV': '"production"', 'import.meta.env': JSON.stringify({ DEV: false }) },
})
const assets = resolve(root, 'frontend/dist/assets')
const css = await readFile(resolve(assets, (await readdir(assets)).find(name => name.endsWith('.css'))), 'utf8')
const inner = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NeuroCare offline design review</title><style>${css}</style></head><body><div id="review-root"></div><script>${result.outputFiles[0].text.replace(/<\/script/gi, '<\\/script')}<\/script></body></html>`
const encoded = JSON.stringify(inner).replace(/</g, '\\u003c')
const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NeuroCare — offline design review</title><style>body{margin:0;background:#e6e2eb;font:12px "Segoe UI",sans-serif;color:#191620}.review-tools{min-height:52px;box-sizing:border-box;display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:8px 16px;padding:8px 14px;background:#292137;color:#fff}.review-tools small{color:#d5c8ec}button{font:inherit;cursor:pointer;background:#fff;color:#191620;border:1px solid #b9aec9;border-radius:5px;min-height:32px;padding:5px 10px}button[aria-pressed=true]{background:#d5c8ec}button:focus-visible{outline:2px solid #d5c8ec;outline-offset:3px}iframe{display:block;width:1280px;max-width:100%;height:calc(100vh - 52px);border:0;margin:auto;background:#fbfaff}</style></head><body><div class="review-tools"><strong>OFFLINE DESIGN REVIEW</strong><small>Saved project metadata · No live predictions or writes</small><div>${[[1280,'Desktop'],[768,'Tablet'],[390,'Mobile'],[320,'Small mobile']].map(([width,label])=>`<button type="button" data-width="${width}" aria-pressed="${width===1280}">${label}</button>`).join(' ')}</div><output id="viewport"></output></div><iframe title="Actual NeuroCare React components" id="review-frame"></iframe><script>const frame=document.getElementById('review-frame');frame.srcdoc=${encoded};const measure=()=>document.getElementById('viewport').textContent=frame.clientWidth+'px';for(const button of document.querySelectorAll('button[data-width]'))button.onclick=()=>{frame.style.width=button.dataset.width+'px';for(const other of document.querySelectorAll('button[data-width]'))other.setAttribute('aria-pressed',String(other===button));measure()};window.addEventListener('resize',measure);measure();<\/script></body></html>`
await writeFile(resolve(directory, 'review.html'), html)
console.log('Offline design review created. It uses genuine saved metadata and never sends a prediction.')
