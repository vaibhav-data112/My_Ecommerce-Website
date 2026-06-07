import client from './client'
import axios from 'axios'

export const getDashboard     = ()           => client.get('/admin')
export const getProducts      = ()           => client.get('/admin/products')
export const getProduct       = (id)         => client.get(`/admin/products/${id}`)
export const addProduct       = (form)       => axios.post('/api/admin/products/add', form, { withCredentials: true })
export const editProduct      = (id, form)   => axios.post(`/api/admin/products/${id}/edit`, form, { withCredentials: true })
export const deleteProduct    = (id)         => client.post(`/admin/products/${id}/delete`)
export const getOrders        = ()           => client.get('/admin/orders')
export const updateOrderStatus = (id, data)  => client.post(`/admin/orders/${id}/status`, data)
