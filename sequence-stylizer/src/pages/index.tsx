import Image from 'next/image'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export default function Home() {
  return (
    <main
      className={`flex min-h-screen flex-col items-center ${inter.className} p-40 gap-y-10`}
    >
      <div className={`absolute inset-0 bg-gradient-to-b from-black from-40% to-black/[.7] min-h-screen min-w-screen`}>

      </div>
      <div className={`absolute top-0 left-0 right-0 bottom-0 bg-cloud-bg -z-10`}>

      </div>
      <div className="rainbow z-10">
        Welcome
      </div>
      <button className={`inline-flex flex-wrap items-center border-2 w-auto p-1 px-2 rounded-lg text-lg cursor-pointer z-10`}>
        Upload
      </button>
    </main>
  )
}
