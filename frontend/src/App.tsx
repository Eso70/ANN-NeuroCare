import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppLayout } from './layouts/AppLayout'
import { Dashboard } from './pages/Dashboard'
import { Prediction } from './pages/Prediction'
import { NotFound } from './pages/NotFound'
import { ModelPage } from './pages/ModelPage'
import { About } from './pages/About'

export default function App() {
  return <BrowserRouter><Routes><Route element={<AppLayout />}><Route index element={<Dashboard />} /><Route path="predictions" element={<Prediction />} /><Route path="model" element={<ModelPage />} /><Route path="about" element={<About />} /><Route path="*" element={<NotFound />} /></Route></Routes></BrowserRouter>
}
