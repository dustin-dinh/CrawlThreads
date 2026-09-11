import { expect, test } from '@playwright/test'

test('demo discovery, inbox review, and idea workflow', async ({page}) => {
  await page.goto('/')
  if (await page.getByText('Thiết lập Story Miner lần đầu').isVisible().catch(()=>false)) {
    for (let i=0;i<4;i++) await page.getByRole('button',{name:/Tiếp tục/}).click()
    await page.getByRole('button',{name:/Vào ứng dụng/}).click()
  }
  await expect(page.getByRole('heading',{name:'Tổng quan'})).toBeVisible()
  await page.getByRole('link',{name:'Khám phá'}).click()
  await expect(page.getByRole('heading',{name:'Khám phá câu chuyện'})).toBeVisible()
  await page.getByRole('button',{name:/Tìm kiếm/}).click()
  await expect(page.getByText(/Đã thêm \d+ kết quả mới/)).toBeVisible()
  await page.getByRole('link',{name:'Kho truyện'}).click()
  await expect(page.locator('.story-card').first()).toBeVisible()
  await page.locator('.story-card').first().getByRole('link',{name:'Mở'}).click()
  await expect(page.getByText('Nguồn gốc')).toBeVisible()
  await page.getByRole('button',{name:/Lưu vào backlog/}).click()
  await page.getByRole('button',{name:/Tạo ý tưởng nội dung/}).click()
  await expect(page.getByRole('heading',{name:'Ý tưởng nội dung'})).toBeVisible()
  await expect(page.locator('.idea-card').first()).toBeVisible()
})
