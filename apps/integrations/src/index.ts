import Fastify from 'fastify'

const app = Fastify({ logger: true })

app.post('/ats/:vendor/sync-candidate', async (req: any, res) => {
  const { vendor } = req.params as { vendor: string }
  const body = req.body as any
  // TODO: fetch resume.json + pdf from API and push to vendor
  app.log.info({ vendor, body }, 'sync-candidate requested')
  return { ok: true }
})

app.post('/ats/:vendor/webhook', async (req: any, res) => {
  const { vendor } = req.params as { vendor: string }
  app.log.info({ vendor, body: req.body }, 'webhook received')
  return { ok: true }
})

app.listen({ port: 8700, host: '0.0.0.0' })
  .then(() => app.log.info('Integrations gateway running on :8700'))
  .catch((e) => { app.log.error(e); process.exit(1) })
