import client from './client'

export const getWishlist       = ()       => client.get('/wishlist')
export const toggleWishlist    = (data)   => client.post('/wishlist/toggle', data)
export const wishlistAddToCart = (data)   => client.post('/wishlist/add-to-cart', data)
