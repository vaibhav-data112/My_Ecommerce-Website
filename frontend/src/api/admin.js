import client from './client'

export const getDashboard      = ()           => client.get('/admin')
export const getProducts       = ()           => client.get('/admin/products')
export const getProduct        = (id)         => client.get(`/admin/products/${id}`)
export const addProduct        = (form)       => client.post('/admin/products/add', form)
export const editProduct       = (id, form)   => client.post(`/admin/products/${id}/edit`, form)
export const deleteProduct     = (id)         => client.post(`/admin/products/${id}/delete`)
export const getOrders         = ()           => client.get('/admin/orders')
export const updateOrderStatus = (id, data)   => client.post(`/admin/orders/${id}/status`, data)
export const getReturns        = ()           => client.get('/admin/returns')
export const approveReturn     = (id)         => client.post(`/admin/orders/${id}/return-approve`)
export const rejectReturn      = (id, reason) => client.post(`/admin/orders/${id}/return-reject`, { reason })
export const processRefund     = (id)         => client.post(`/admin/orders/${id}/refund`)
