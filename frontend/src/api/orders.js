import client from './client'

export const getCheckoutInfo  = ()        => client.get('/checkout')
export const placeOrder       = (data)    => client.post('/checkout', data)
export const getPaymentInfo   = (id)      => client.get(`/payment/${id}`)
export const verifyPayment    = (data)    => client.post('/payment/verify', data)
export const getOrders        = ()        => client.get('/orders')
export const getOrder         = (id)      => client.get(`/orders/${id}`)
