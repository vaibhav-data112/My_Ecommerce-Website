import client from './client'

export const submitContact  = (data)   => client.post('/contact', data)
export const getContacts    = (status) => client.get('/admin/contacts',
                                            { params: status ? { status } : {} })
export const resolveContact = (id)     => client.patch(`/admin/contacts/${id}/resolve`)
