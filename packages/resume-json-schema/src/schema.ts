import Ajv from 'ajv'
import addFormats from 'ajv-formats'

export const resumeSchemaV0 = {
  $id: 'https://work.id/schemas/resume.v0.json',
  type: 'object',
  required: ['person', 'trust', 'skills', 'experiences', 'projects', 'links', 'meta'],
  properties: {
    person: {
      type: 'object',
      required: ['name', 'headline'],
      properties: {
        name: { type: 'string' },
        headline: { type: 'string' },
        location: { type: 'string', nullable: true },
        public_contacts: { type: 'array', items: { type: 'string' }, nullable: true },
      },
    },
    trust: {
      type: 'object',
      required: ['score', 'breakdown'],
      properties: {
        score: { type: 'integer', minimum: 0, maximum: 100 },
        breakdown: {
          type: 'object',
          required: ['verified', 'corroborated', 'self'],
          properties: {
            verified: { type: 'number' },
            corroborated: { type: 'number' },
            self: { type: 'number' },
          },
        },
      },
    },
    skills: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'verified', 'evidenceRefs'],
        properties: {
          name: { type: 'string' },
          level: { type: 'string', nullable: true },
          verified: { type: 'boolean' },
          evidenceRefs: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    experiences: {
      type: 'array',
      items: {
        type: 'object',
        required: ['role', 'startDate', 'highlights', 'verificationStatus', 'evidenceRefs'],
        properties: {
          role: { type: 'string' },
          org: { type: 'string', nullable: true },
          startDate: { type: 'string' },
          endDate: { type: 'string', nullable: true },
          highlights: { type: 'array', items: { type: 'string' } },
          verificationStatus: { type: 'string' },
          evidenceRefs: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    education: {
      type: 'array',
      items: {
        type: 'object',
        required: ['school', 'startDate', 'verificationStatus'],
        properties: {
          school: { type: 'string' },
          degree: { type: 'string', nullable: true },
          startDate: { type: 'string' },
          endDate: { type: 'string', nullable: true },
          verificationStatus: { type: 'string' },
        },
      },
    },
    projects: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'summary', 'links', 'evidenceRefs'],
        properties: {
          name: { type: 'string' },
          summary: { type: 'string' },
          links: { type: 'array', items: { type: 'string' } },
          evidenceRefs: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    verifications: {
      type: 'array',
      items: {
        type: 'object',
        required: ['type', 'status', 'confidence', 'issuer', 'issuedAt', 'evidenceRefs'],
        properties: {
          type: { type: 'string' },
          status: { type: 'string' },
          confidence: { type: 'number' },
          issuer: { type: 'string' },
          issuedAt: { type: 'string' },
          evidenceRefs: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    links: {
      type: 'object',
      required: ['publicCardUrl'],
      properties: {
        publicCardUrl: { type: 'string' },
        smartLinks: {
          type: 'object',
          properties: {
            backend: { type: 'string', nullable: true },
            frontend: { type: 'string', nullable: true },
          },
        },
        qrPng: { type: 'string', nullable: true },
      },
    },
    meta: {
      type: 'object',
      required: ['cardId', 'version', 'generatedAt'],
      properties: {
        cardId: { type: 'string' },
        version: { type: 'string' },
        generatedAt: { type: 'string' },
      },
    },
  },
}

const ajv = new Ajv({ allErrors: true })
addFormats(ajv)
const validate = ajv.compile(resumeSchemaV0)

export function validateResumeJson(data: unknown): { valid: boolean; errors?: any } {
  const valid = validate(data)
  return { valid: !!valid, errors: validate.errors }
}
