import Head from 'next/head'
import Header from '@/components/Header'
import Footer from '@/components/Footer'

export default function Terms() {
  return (
    <>
      <Head>
        <title>Terms of Service - Knocodex</title>
        <meta name="description" content="Terms of Service for Knocodex" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Header />

      <main className="container mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        
        <div className="prose prose-invert max-w-none">
          <p>Last updated: May 21, 2023</p>
          
          <h2>Introduction</h2>
          <p>
            These terms and conditions outline the rules and regulations for the use of Knocodex's website
            and services. By accessing this website or using our services, we assume you accept these terms
            and conditions in full. Do not continue to use Knocodex's website or services if you do not
            accept all of the terms and conditions stated on this page.
          </p>
          
          <h2>License</h2>
          <p>
            Knocodex is licensed under the MIT License. This means you are free to:
          </p>
          <ul>
            <li>Use the software for any purpose</li>
            <li>Change the software to suit your needs</li>
            <li>Share the software with anyone</li>
            <li>Distribute the software to anyone</li>
          </ul>
          <p>
            Subject to the following conditions:
          </p>
          <ul>
            <li>The above copyright notice and this permission notice shall be included in all
              copies or substantial portions of the Software.</li>
          </ul>
          <p>
            THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
            INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
            PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
            FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
            OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
            DEALINGS IN THE SOFTWARE.
          </p>
          
          <h2>Website Use</h2>
          <p>
            The following behaviors are prohibited when using our website:
          </p>
          <ul>
            <li>Using the website in any way that causes, or may cause, damage to the website or
              impairment of the availability or accessibility of the website.</li>
            <li>Using this website in any way that is unlawful, illegal, fraudulent, or harmful.</li>
            <li>Using this website to copy, store, host, transmit, send, use, publish, or distribute
              any material which consists of (or is linked to) any spyware, computer virus, Trojan
              horse, worm, keystroke logger, rootkit, or other malicious computer software.</li>
            <li>Conducting any systematic or automated data collection activities on or in relation
              to this website without express written consent.</li>
          </ul>
          
          <h2>Service Use</h2>
          <p>
            When using Knocodex services:
          </p>
          <ul>
            <li>You are responsible for maintaining the security of your account and API keys.</li>
            <li>You are responsible for all activities that occur under your account.</li>
            <li>You must not use the service for any illegal or unauthorized purpose.</li>
            <li>You must not, in the use of the service, violate any laws in your jurisdiction.</li>
          </ul>
          
          <h2>Limitation of Liability</h2>
          <p>
            In no event shall Knocodex, nor its directors, employees, partners, agents, suppliers, or
            affiliates, be liable for any indirect, incidental, special, consequential or punitive
            damages, including without limitation, loss of profits, data, use, goodwill, or other
            intangible losses, resulting from:
          </p>
          <ul>
            <li>Your access to or use of or inability to access or use the service.</li>
            <li>Any conduct or content of any third party on the service.</li>
            <li>Any content obtained from the service.</li>
            <li>Unauthorized access, use, or alteration of your transmissions or content.</li>
          </ul>
          
          <h2>Changes to Terms</h2>
          <p>
            We reserve the right, at our sole discretion, to modify or replace these Terms at any time.
            If a revision is material we will provide at least 30 days' notice prior to any new terms
            taking effect. What constitutes a material change will be determined at our sole discretion.
          </p>
          
          <h2>Contact Us</h2>
          <p>
            If you have any questions about these Terms, please contact us at terms@knocodex.dev.
          </p>
        </div>
      </main>

      <Footer />
    </>
  )
}
