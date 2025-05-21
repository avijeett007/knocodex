import Head from 'next/head'
import Header from '@/components/Header'
import Footer from '@/components/Footer'

export default function Privacy() {
  return (
    <>
      <Head>
        <title>Privacy Policy - Knocodex</title>
        <meta name="description" content="Privacy Policy for Knocodex" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Header />

      <main className="container mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
        
        <div className="prose prose-invert max-w-none">
          <p>Last updated: May 21, 2023</p>
          
          <h2>Introduction</h2>
          <p>
            At Knocodex, we respect your privacy and are committed to protecting your personal data.
            This privacy policy will inform you about how we look after your personal data when you
            visit our website and tell you about your privacy rights and how the law protects you.
          </p>
          
          <h2>Data We Collect</h2>
          <p>
            We may collect, use, store and transfer different kinds of personal data about you which
            we have grouped together as follows:
          </p>
          <ul>
            <li><strong>Identity Data</strong> includes first name, last name, username or similar identifier.</li>
            <li><strong>Contact Data</strong> includes email address.</li>
            <li><strong>Technical Data</strong> includes internet protocol (IP) address, browser type and version,
              time zone setting and location, browser plug-in types and versions, operating system and platform,
              and other technology on the devices you use to access this website.</li>
            <li><strong>Usage Data</strong> includes information about how you use our website and services.</li>
          </ul>
          
          <h2>How We Use Your Data</h2>
          <p>
            We will only use your personal data when the law allows us to. Most commonly, we will use
            your personal data in the following circumstances:
          </p>
          <ul>
            <li>To register you as a new customer or user.</li>
            <li>To provide you with information, products, or services that you request from us.</li>
            <li>To notify you about changes to our service.</li>
            <li>To administer and protect our business and this website.</li>
            <li>To deliver relevant website content to you.</li>
            <li>To use data analytics to improve our website, products/services, marketing, customer
              relationships, and experiences.</li>
          </ul>
          
          <h2>Data Security</h2>
          <p>
            We have put in place appropriate security measures to prevent your personal data from being
            accidentally lost, used, or accessed in an unauthorized way, altered, or disclosed. In addition,
            we limit access to your personal data to those employees, agents, contractors, and other third
            parties who have a business need to know.
          </p>
          
          <h2>Data Retention</h2>
          <p>
            We will only retain your personal data for as long as reasonably necessary to fulfill the
            purposes we collected it for, including for the purposes of satisfying any legal, regulatory,
            tax, accounting, or reporting requirements.
          </p>
          
          <h2>Your Legal Rights</h2>
          <p>
            Under certain circumstances, you have rights under data protection laws in relation to your
            personal data, including the right to:
          </p>
          <ul>
            <li>Request access to your personal data.</li>
            <li>Request correction of your personal data.</li>
            <li>Request erasure of your personal data.</li>
            <li>Object to processing of your personal data.</li>
            <li>Request restriction of processing your personal data.</li>
            <li>Request transfer of your personal data.</li>
            <li>Right to withdraw consent.</li>
          </ul>
          
          <h2>Changes to This Privacy Policy</h2>
          <p>
            We may update our privacy policy from time to time. We will notify you of any changes by
            posting the new privacy policy on this page and updating the "Last updated" date at the top
            of this privacy policy.
          </p>
          
          <h2>Contact Us</h2>
          <p>
            If you have any questions about this privacy policy or our privacy practices, please contact
            us at privacy@knocodex.dev.
          </p>
        </div>
      </main>

      <Footer />
    </>
  )
}
