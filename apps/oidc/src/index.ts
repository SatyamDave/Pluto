import Fastify from 'fastify'
import { generateKeyPair, exportJWK } from 'jose'

const app = Fastify({ logger: true })

let jwk: any
let kid = 'dev-kid'

app.get('/.well-known/openid-configuration', async () => ({
  issuer: process.env.OIDC_ISSUER || 'http://localhost:8800',
  authorization_endpoint: '/authorize',
  token_endpoint: '/token',
  userinfo_endpoint: '/userinfo',
  jwks_uri: '/.well-known/jwks.json',
  response_types_supported: ['code'],
  subject_types_supported: ['public'],
  id_token_signing_alg_values_supported: ['RS256'],
  scopes_supported: ['openid', 'profile', 'work_card.basic', 'work_card.verified_claims'],
}))

app.get('/.well-known/jwks.json', async () => ({ keys: [jwk] }))

async function boot() {
  const { publicKey } = await generateKeyPair('RS256')
  jwk = await exportJWK(publicKey)
  jwk.kid = kid

  await app.listen({ port: 8800, host: '0.0.0.0' })
  app.log.info('OIDC provider running on :8800')
}

boot().catch((e) => { app.log.error(e); process.exit(1) })
