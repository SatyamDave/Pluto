import { chromium } from 'playwright'
import QRCode from 'qrcode'

export async function renderPdf(resumeJson: any): Promise<Buffer> {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1200, height: 1600 } })

  const qr = resumeJson?.links?.publicCardUrl ? await QRCode.toDataURL(resumeJson.links.publicCardUrl) : ''
  const html = `<!doctype html>
  <html><head><meta charset="utf-8"><style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 32px; }
  h1 { margin: 0 0 8px; }
  .muted { color: #666; }
  .chip { display: inline-block; border: 1px solid #ddd; border-radius: 6px; padding: 2px 8px; margin: 2px; }
  .col { display: inline-block; vertical-align: top; }
  .left { width: 65%; }
  .right { width: 30%; margin-left: 5%; }
  hr { border: none; border-top: 1px solid #eee; margin: 12px 0; }
  </style></head><body>
  <h1>${escapeHtml(resumeJson.person?.name || '')}</h1>
  <div class="muted">${escapeHtml(resumeJson.person?.headline || '')}</div>
  <div class="muted">Trust Score: ${resumeJson.trust?.score ?? ''}</div>
  <hr/>
  <div class="col left">
    <h3>Experience</h3>
    ${(resumeJson.experiences || []).slice(0,5).map((e: any) => `<div><strong>${escapeHtml(e.role)}</strong> ${e.org ? ' @ ' + escapeHtml(e.org) : ''}<div class="muted">${escapeHtml(e.startDate)} - ${escapeHtml(e.endDate || 'Present')}</div><ul>${(e.highlights||[]).slice(0,3).map((h: string)=>`<li>${escapeHtml(h)}</li>`).join('')}</ul></div>`).join('')}
    <h3>Projects</h3>
    ${(resumeJson.projects || []).slice(0,3).map((p: any)=>`<div><strong>${escapeHtml(p.name)}</strong><div class="muted">${escapeHtml(p.summary||'')}</div></div>`).join('')}
  </div>
  <div class="col right">
    <h3>Top Skills</h3>
    <div>${(resumeJson.skills||[]).slice(0,10).map((s:any)=>`<span class="chip">${escapeHtml(s.name)}</span>`).join('')}</div>
    ${qr ? `<img src="${qr}" width="140"/>` : ''}
  </div>
  </body></html>`

  await page.setContent(html, { waitUntil: 'networkidle' })
  const pdf = await page.pdf({ format: 'A4', printBackground: true })
  await browser.close()
  return Buffer.from(pdf)
}

function escapeHtml(s: string) {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' } as any)[c])
}
