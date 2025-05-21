import type { NextApiRequest, NextApiResponse } from 'next'
import { addToWaitlist } from '@/lib/supabase'

type ResponseData = {
  success: boolean
  message?: string
  error?: any
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData>
) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, message: 'Method not allowed' })
  }

  try {
    const { email, name } = req.body

    if (!email) {
      return res.status(400).json({ success: false, message: 'Email is required' })
    }

    const result = await addToWaitlist(email, name)

    if (!result.success) {
      return res.status(500).json({ 
        success: false, 
        message: 'Failed to add to waitlist',
        error: result.error
      })
    }

    return res.status(200).json({ success: true, message: 'Successfully added to waitlist' })
  } catch (error) {
    console.error('Waitlist API error:', error)
    return res.status(500).json({ 
      success: false, 
      message: 'Internal server error',
      error
    })
  }
}
