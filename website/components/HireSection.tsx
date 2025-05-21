import React from 'react'

const HireSection = () => {
  return (
    <div className="bg-primary-900/30 rounded-lg p-8 border border-primary-500/30">
      <h2 className="text-3xl font-bold mb-4">Hire Knocodex+ for Your Development</h2>
      <p className="text-lg mb-6">
        Need specialized AI development expertise? Our team can help you implement Knocodex in your organization and customize it for your specific needs.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-black/50 p-6 rounded-lg border border-primary-500/20">
          <h3 className="text-xl font-bold mb-2">Enterprise Support</h3>
          <p>Get dedicated support, training, and maintenance for your Knocodex implementation.</p>
        </div>
        
        <div className="bg-black/50 p-6 rounded-lg border border-primary-500/20">
          <h3 className="text-xl font-bold mb-2">Custom Development</h3>
          <p>We'll build custom features and integrations tailored to your specific workflow and requirements.</p>
        </div>
        
        <div className="bg-black/50 p-6 rounded-lg border border-primary-500/20">
          <h3 className="text-xl font-bold mb-2">AI Consulting</h3>
          <p>Get expert advice on implementing AI in your development process and maximizing its benefits.</p>
        </div>
      </div>
      
      <div className="text-center">
        <a 
          href="mailto:services@knocodex.dev" 
          className="btn-primary inline-block"
        >
          Contact Us for Details
        </a>
      </div>
    </div>
  )
}

export default HireSection
