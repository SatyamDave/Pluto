import { test, expect } from '@playwright/test'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const WEB = process.env.NEXT_PUBLIC_WEB_URL || 'http://localhost:3000'

test.describe('Public card', () => {
  test('loads demo card and answers chat', async ({ page, request }) => {
    await page.goto(`${WEB}/u/demo-dev`)
    await expect(page.getByText('Trust Score:')).toBeVisible()

    await page.fill('textarea', 'Does this candidate know React + AWS?')
    await page.click('text=Ask')
    await expect(page.getByText('Based on verified facts').or(page.getByText('candidate has strong React'))).toBeVisible()
  })
})
