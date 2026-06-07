import client from './client'

export const getMe      = ()       => client.get('/auth/me')
export const login      = (data)   => client.post('/auth/login', data)
export const signup     = (data)   => client.post('/auth/signup', data)
export const logout     = ()       => client.post('/auth/logout')
