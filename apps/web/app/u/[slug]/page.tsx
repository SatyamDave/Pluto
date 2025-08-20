import { Metadata } from 'next'
import { notFound } from 'next/navigation'

async function getProjection(slug: string) {
  const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const res = await fetch(`${api}/public/cards/${slug}`, { cache: 'no-store' })
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Failed to load card')
  return res.json()
}

async function getMeta(slug: string) {
  const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const res = await fetch(`${api}/public/cards/${slug}/meta`, { cache: 'no-store' })
  if (!res.ok) return { title: 'Work Identity Card', description: '', image: '' }
  return res.json()
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const meta = await getMeta(params.slug)
  return { title: meta.title, description: meta.description, openGraph: { images: [meta.image] } }
}

export default async function PublicCardPage({ params }: { params: { slug: string } }) {
  const data = await getProjection(params.slug)
  if (!data) return notFound()

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      <div className="container-wide py-10">
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{data.headline}</h1>
              <p className="text-gray-600 dark:text-gray-300">{data.role_fit_summary}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="trust-score trust-score-high">Trust Score: {data.trust_score}</span>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-6">
              <section className="card p-6">
                <h2 className="card-title mb-4">Top Skills</h2>
                <div className="flex flex-wrap gap-2">
                  {data.top_skills.map((s: string) => (<span key={s} className="skill-tag">{s}</span>))}
                </div>
              </section>

              <section className="card p-6">
                <h2 className="card-title mb-4">Highlights</h2>
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-200">
                  {data.highlights.map((h: string, i: number) => (<li key={i}>{h}</li>))}
                </ul>
              </section>

              <section className="card p-6">
                <h2 className="card-title mb-4">Ask about this candidate</h2>
                <ChatBox slug={params.slug} />
              </section>
            </div>
            <div className="space-y-6">
              <section className="card p-6">
                <h3 className="card-title mb-4">Verification</h3>
                <div className="flex flex-wrap gap-2">
                  {data.verification_badges.map((b: string, i: number) => (<span key={i} className="verification-badge verification-badge-verified">{b}</span>))}
                </div>
              </section>

              <section className="card p-6">
                <h3 className="card-title mb-4">Contact</h3>
                <div className="flex flex-col gap-2">
                  <a className="btn btn-primary" href={`mailto:?subject=Candidate%20${encodeURIComponent(data.headline)}&body=${encodeURIComponent('Check this card: ' + (process.env.NEXT_PUBLIC_WEB_URL || 'http://localhost:3000') + '/u/' + params.slug)}`}>Email card to self</a>
                  <a className="btn btn-outline" href={`/api/download/${params.slug}`}>Download PDF card</a>
                  <a className="btn btn-secondary" href={`/request-intro/${params.slug}`}>Request intro</a>
                </div>
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

'use client'
import { useState } from 'react'

function ChatBox({ slug }: { slug: string }) {
  const [q, setQ] = useState('')
  const [a, setA] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function ask() {
    setLoading(true); setA(null)
    const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const res = await fetch(`${api}/public/cards/${slug}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q }) })
    if (res.ok) {
      const data = await res.json()
      setA(data.answer)
    } else if (res.status === 429) {
      setA('Rate limit exceeded. Please try again later.')
    } else {
      setA('Sorry, something went wrong.')
    }
    setLoading(false)
  }

  return (
    <div className="space-y-3">
      <textarea className="input" rows={3} placeholder="Does this candidate know React + AWS?" value={q} onChange={(e) => setQ(e.target.value)} />
      <button className="btn btn-primary" onClick={ask} disabled={loading || !q.trim()}>{loading ? 'Asking...' : 'Ask'}</button>
      {a && <div className="mt-2 text-gray-800 dark:text-gray-100">{a}</div>}
    </div>
  )
}
