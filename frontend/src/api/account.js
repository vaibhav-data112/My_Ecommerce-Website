import client from './client'
import axios from 'axios'

export const getDashboard          = ()       => client.get('/account')
export const getProfile            = ()       => client.get('/account/profile')
export const updateProfile         = (form)   => axios.post('/api/account/profile', form, { withCredentials: true })
export const deleteAvatar          = ()       => client.post('/account/profile/delete-avatar')
export const getAddresses          = ()       => client.get('/account/addresses')
export const addAddress            = (data)   => client.post('/account/addresses/new', data)
export const updateAddress         = (id, d)  => client.put(`/account/addresses/${id}`, d)
export const deleteAddress         = (id)     => client.post(`/account/addresses/${id}/delete`)
export const setDefaultAddress     = (id)     => client.post(`/account/addresses/${id}/default`)
export const getSettings           = ()       => client.get('/account/settings')
export const changePassword        = (data)   => client.post('/account/settings/password', data)
export const updateNotifications   = (data)   => client.post('/account/settings/notifications', data)
