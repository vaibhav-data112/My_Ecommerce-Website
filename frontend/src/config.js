// WhatsApp owner number: country code + number, no +, no spaces (e.g. 919876543210)
export const WHATSAPP_NUMBER = '919336768655'

const _prefill = [
  'Namaste Karvii Spices',
  '',
  'Mujhe apne order mein problem hai.',
  'Order no: ____',
  'Problem: ____',
  '(Photo neeche bhej raha/rahi hun)',
].join('\n')

export const WHATSAPP_URL =
  `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(_prefill)}`
