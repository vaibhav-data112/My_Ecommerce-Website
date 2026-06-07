import client from './client'

export const getFeatured  = ()           => client.get('/')
export const getProducts  = (params)     => client.get('/products', { params })
export const getProduct   = (id)         => client.get(`/products/${id}`)
export const addReview    = (id, data)   => client.post(`/products/${id}/review`, data)
export const editReview   = (id, data)   => client.post(`/reviews/${id}/edit`, data)
export const deleteReview = (id)         => client.post(`/reviews/${id}/delete`)
