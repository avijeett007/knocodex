import { useState } from 'react'
import { createClient } from '@supabase/supabase-js'

const WaitlistForm = () => {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email) {
      setError('Please enter your email address')
      return
    }
    
    setLoading(true)
    setError('')
    
    try {
      // In a real implementation, this would use actual Supabase credentials
      // For demo purposes, we're just simulating the API call
      
      // const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
      // const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
      // const supabase = createClient(supabaseUrl, supabaseKey)
      
      // const { error } = await supabase
      //   .from('waitlist')
      //   .insert([{ email, name, created_at: new Date() }])
      
      // if (error) throw error
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setSuccess(true)
      setEmail('')
      setName('')
    } catch (err) {
      console.error('Error submitting to waitlist:', err)
      setError('Failed to join waitlist. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="waitlist-form">
      {success ? (
        <div className="text-center">
          <h3 className="text-xl font-bold mb-2 text-primary-500">Thank you for joining!</h3>
          <p className="mb-4">We'll keep you updated on our progress and let you know when Knocodex has new features.</p>
          <button 
            className="btn-secondary"
            onClick={() => setSuccess(false)}
          >
            Join with another email
          </button>
        </div>
      ) : (
        <>
          <h3 className="text-xl font-bold mb-4">Join the Knocodex Waitlist</h3>
          <p className="mb-4">Be the first to know when we launch new features and updates.</p>
          
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="name" className="block mb-2">Name</label>
              <input
                type="text"
                id="name"
                className="w-full px-4 py-2 bg-black/50 border border-gray-700 rounded focus:outline-none focus:border-primary-500"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            
            <div className="mb-4">
              <label htmlFor="email" className="block mb-2">Email *</label>
              <input
                type="email"
                id="email"
                className="w-full px-4 py-2 bg-black/50 border border-gray-700 rounded focus:outline-none focus:border-primary-500"
                placeholder="your@email.com"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            
            {error && (
              <div className="mb-4 text-red-500">
                {error}
              </div>
            )}
            
            <button
              type="submit"
              className="btn-primary w-full"
              disabled={loading}
            >
              {loading ? 'Joining...' : 'Join Waitlist'}
            </button>
          </form>
        </>
      )}
    </div>
  )
}

export default WaitlistForm
