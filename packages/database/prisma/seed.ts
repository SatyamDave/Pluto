import { PrismaClient, ClaimType, CardType } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  // Users
  const user = await prisma.user.upsert({
    where: { email: 'demo@identity.me' },
    update: {},
    create: {
      email: 'demo@identity.me',
      name: 'Demo Dev',
      username: 'demodev',
      location: 'SF, CA',
    },
  })

  // Claims (verified skills & projects)
  const skillReact = await prisma.claim.create({
    data: {
      userId: user.id,
      type: 'SKILL',
      category: 'WORK',
      title: 'React',
      description: 'Verified React skill',
      content: { skill: 'React', proficiency_level: 'Advanced', proof_sources: ['github_repo:demo/react-app'] },
      confidence: 0.9,
      isVerified: true,
      proofSources: ['github_repo:demo/react-app'],
    },
  })

  const skillAWS = await prisma.claim.create({
    data: {
      userId: user.id,
      type: 'SKILL',
      category: 'WORK',
      title: 'AWS',
      description: 'Verified AWS skill',
      content: { skill: 'AWS', proficiency_level: 'Advanced', proof_sources: ['github_repo:demo/iac'] },
      confidence: 0.88,
      isVerified: true,
      proofSources: ['github_repo:demo/iac'],
    },
  })

  const project = await prisma.claim.create({
    data: {
      userId: user.id,
      type: 'PROJECT',
      category: 'WORK',
      title: 'AWS deployment pipeline',
      description: 'CI/CD on AWS',
      content: { name: 'AWS deployment pipeline', technologies: ['AWS', 'Terraform'] },
      confidence: 0.9,
      isVerified: true,
      proofSources: ['github_repo:demo/iac'],
    },
  })

  // Card
  const card = await prisma.identityCard.create({
    data: {
      userId: user.id,
      type: 'WORK',
      title: 'Full-Stack Engineer',
      subtitle: 'React • Node • AWS',
      template: 'default',
      isPublic: true,
      shareSlug: 'demo-dev',
      claims: { connect: [{ id: skillReact.id }, { id: skillAWS.id }, { id: project.id }] },
      settings: { availability: 'Open to full-time', location: 'Remote' },
    },
  })

  console.log('Seeded demo card:', card.shareSlug)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect() })
