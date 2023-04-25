import Image from 'next/image'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export default function Home() {
  return (
    <main
      className={`flex min-h-screen flex-col items-center ${inter.className} p-40 gap-y-10`}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-black from-40% to-black/[.7] min-h-screen min-w-screen"/>
      <div className="absolute top-0 left-0 right-0 bottom-0 bg-cloud-bg -z-10"/>

      <div className="absolute top-4 left-4 text-white font-bold text-lg">
        Sequence Stylizers
      </div>
      <div className="rainbow z-10">
        Welcome
      </div>

      <div className="flex items-center justify-center z-10 w-1/3">
        <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-gray-800 border-gray-600 hover:border-blue-700">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <svg aria-hidden="true" className="w-10 h-10 mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                </svg>
                <p className="mb-2 text-sm text-gray-500 dark:text-gray-400"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">MP4 and JPG</p>
            </div>
            <input id="dropzone-file" type="file" multiple className="hidden" />
        </label>
      </div> 

    </main>
  )
}
