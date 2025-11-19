import Navbar from './Navbar'
import Footer from './Footer'

function Layout({ children, onCreatePost }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex flex-col">
      <Navbar />
      <main className="flex-1 pt-20 pb-24 overflow-y-auto">
        {children}
      </main>
      <Footer onCreatePost={onCreatePost} />
    </div>
  )
}

export default Layout

