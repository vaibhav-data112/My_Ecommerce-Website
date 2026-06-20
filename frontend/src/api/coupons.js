import client from './client'

export const validateCoupon = (code, subtotal) =>
  client.post('/coupons/validate', { code, subtotal })
