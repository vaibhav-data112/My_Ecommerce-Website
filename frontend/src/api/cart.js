import client from './client'

export const getCart      = ()       => client.get('/cart')
export const addToCart    = (data)   => client.post('/cart/add', data)
export const updateCart   = (data)   => client.post('/cart/update', data)
export const removeFromCart = (data) => client.post('/cart/remove', data)
