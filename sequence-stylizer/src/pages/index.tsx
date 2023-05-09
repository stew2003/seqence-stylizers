import React, { ChangeEvent, useRef, useState } from "react"
import { UploadResponseType } from "./api/upload"
import { TransferResponseType } from "./api/transfer"
import Link from "next/link"
import Loading from "@component/components/loading"
import LoadingAll from "@component/components/LoadingAll"
import SERVER_URL, { IMAGE_OUTPUT, MOVIE_OUTPUT } from "@component/utils/globals"

interface FileStorage {
  file: File
  uploaded: boolean
}

export default function Home() {
  const [loading, setLoading] = useState(false)
  const [files, setFiles] = useState<FileStorage[]>([])
  const [previewUrls, setPreviewUrls] = useState<string[]>([])
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null)
  const [downloadThumbnail, setDownloadThumbnail] = useState<string | null>(null)
  const [imagePaths, setImagePaths] = useState<string[]>([])
  const [transfer, setTransfer] = useState<string | null>(null)
  const [show, setShow] = useState<boolean>(true)
  const [lock, setLock] = useState<boolean>(false)

  const onFileUploadChange = (e: ChangeEvent<HTMLInputElement>) => {
    // file upload handler
    e.preventDefault()
    const fileInput = e.target

    if (lock) {
      alert("Wait for current upload to finish")
      return
    }

    if (!fileInput.files) {
      alert("No file was chosen")
      resetInput(e)
      return
    }

    if (fileInput.files.length === 0) {
      alert("Files list is empty")
      resetInput(e)
      return
    }

    if (fileInput.files.length > 2 || files.length > 1) {
      alert("Too many images. Only upload an image or video and a starting image")
      resetInput(e)
      return
    }

    let index = 1
    let valid = true
    // checks that the first upload stored in files is always only a video or image
    // checks that the second upload stored in files is always an image
    Array.from(fileInput.files).map(file => {
      if (index === 1 && files.length === 0) {
        if (!file.type.startsWith("image") && !file.type.startsWith("video"))  {
          alert(`Upload ${index} is not valid media`)
          valid = false
        }
      } else {
        if (!file.type.startsWith("image"))  {
          alert(`Upload ${index + files.length}, of type ${file.type}, is not a valid image`)
          valid = false
        }
      }
      index += 1
    })
    if (!valid) {
      resetInput(e)
      return
    }

    let new_previews: string[] = []
    let new_files: FileStorage[] = []
    Array.from(fileInput.files).map(file => {
      // extracts thumbnail 1 second in to the video to display preview
      if (file.type.startsWith("video")) {
        const videoUrl = URL.createObjectURL(file)
        const video = document.createElement("video")
        video.src = videoUrl
        video.currentTime = 1.0

        video.addEventListener("seeked", () => {
          const canvas = document.createElement("canvas")
          canvas.width = video.videoWidth
          canvas.height = video.videoHeight

          const ctx = canvas.getContext("2d")
          ctx?.drawImage(video, 0, 0, canvas.width, canvas.height)

          const new_url = canvas.toDataURL()
          setThumbnailUrl(new_url)
          
          // remove extraneous elements
          video.remove()
          canvas.remove()
        })
      } else {
        new_previews.push(URL.createObjectURL(file))
      }

      new_files.push({file: file, uploaded: false})
    })

    setFiles(files.concat(new_files))
    setPreviewUrls(previewUrls.concat(new_previews))

    resetInput(e)
  }

  const resetInput = (e: ChangeEvent<HTMLInputElement>) => {
    // resets file input
    e.currentTarget.type = "text"
    e.currentTarget.type = "file"
  }

  const clearState = () => {
    // clears file memory
    setFiles([])
    setPreviewUrls([])
    setThumbnailUrl(null)
    setDownloadThumbnail(null)
    setImagePaths([])
    setTransfer(null)
    setShow(true)
  }

  const onCancelFile = (e: React.MouseEvent<HTMLButtonElement>) => {
    // cancel button handler
    e.preventDefault()
    clearState()
  }

  const onSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
    // submission button handler
    e.preventDefault()

    const formData = new FormData()
    console.log('submitting upload request')

    // locking file upload
    setLock(true)
    // only uploading files that have not been uploaded
    let uploaded_count = 0
    files.forEach((file) => {
      if (!file.uploaded) {
        formData.append("media", file.file)
      } else {
        uploaded_count += 1
      }
    })

    if (uploaded_count >= 2) {
      alert("Already uploaded 2 files successfully")
      return
    }

    // switch to loading screen and make upload request
    setLoading(true)
    const res = await fetch(SERVER_URL + "upload", {
        method: "POST",
        body: formData,
    })

    const response: UploadResponseType = await res.json()
    // turn off loading screen
    setLoading(false)

    // update image paths state for transfer request
    if (response.error === null) {
      // update uploaded prop
      const new_files: FileStorage[] = [...files]
      new_files.forEach((file) => {
        file.uploaded = true
      })

      setFiles(new_files)

      if (imagePaths.length === 1) {
        setImagePaths(imagePaths.concat(response.data!.url))
      } else if (imagePaths.length === 0) {
        setImagePaths(response.data!.url)
      }
    }

    // unlocking file upload
    setLock(false)

    // will never store more than 2 files
    if (files.length > 2) clearState()
  }

  const onTransfer = async (e: React.MouseEvent<HTMLButtonElement>) => {
    // transfer button handler
    e.preventDefault()

    if (imagePaths.length !== 2) {
      alert("Incorrect number of files")
      return
    }

    if (transfer) {
      setShow(true)
      return
    }
    
    console.log('submitting transfer request')
    // switch to loading screen to make transfer request
    setLoading(true)
    const res = await fetch(SERVER_URL + "transfer", {
      method: "POST",
      body: JSON.stringify(imagePaths),
    })
    
    const response: TransferResponseType = await res.json()
    if (response.data) {
      // print response
      console.log(response.data)
      // continually loop and check status of transfer script every 10 seconds using get request
      const loop_id = setInterval(async () => {
        const get_res = await fetch(SERVER_URL + "transfer", {
          method: "GET",
        })
        const get_response: TransferResponseType = await get_res.json()
        // once script finishes the loop terminates and state is updated
        if (get_response.data?.status !== "") {
          setTransfer(null)
          clearInterval(loop_id)
          if (get_response.data!.status === '--image') setTransfer(IMAGE_OUTPUT) // sets downloable preview to the image
          else { // extract thumbnail from outputted movie
            const video = document.createElement("video")
            video.src = MOVIE_OUTPUT
            video.currentTime = 1.0

            video.addEventListener("seeked", () => {
              const canvas = document.createElement("canvas")
              canvas.width = video.videoWidth
              canvas.height = video.videoHeight

              const ctx = canvas.getContext("2d")
              ctx?.drawImage(video, 0, 0, canvas.width, canvas.height)

              const new_url = canvas.toDataURL()
              setDownloadThumbnail(new_url)
              
              // remove extraneous elements
              video.remove()
              canvas.remove()
            })
            setTransfer(MOVIE_OUTPUT) 
          }
          // Turn off loading screen
          setLoading(false)
        } else if (get_response.error !== null) {
          clearInterval(loop_id)
          console.log(get_response.error)
          alert(get_response.error)
          setLoading(false)
        }
      }, 10000)
    }
  }

  const onDownload = (e: React.MouseEvent<HTMLElement>) => {
    // handles the download of a transfer result
    e.stopPropagation()
    setTransfer(null)
  }

  return (
    <div>
      {
        loading ?
        <LoadingAll/> :
        <>
          {
            (transfer && show) &&
            <div className="absolute top-0 left-0 right-0 bottom-0 bg-black z-50 flex items-center justify-center flex-col bg-opacity-95 gap-8" onClick={() => setShow(false)}>
              <p className="rainbow text-[4rem]">
                Style Transfer Download
              </p>
              <img className="max-w-[50%] max-h-[50%] rounded-lg border-blue-600 border-2" src={downloadThumbnail ? downloadThumbnail : transfer} alt="Image"/>
              <Link href={transfer} target="_blank" download className="cell border-blue-600 border-[0.15rem]" onClick={onDownload}>
                Download
              </Link>
            </div>
          }
          <div
            className="flex min-h-screen max-h-screen overflow-hidden flex-col items-center p-20 gap-y-10"
          >
            <div className="absolute inset-0 bg-gradient-to-b from-black from-40% to-black/[.7] min-h-screen min-w-screen"/>
            <div className="absolute top-0 left-0 right-0 bottom-0 bg-cloud-bg -z-10"/>

            <div className="absolute top-4 left-4 text-white font-bold text-lg">
              Sequence Stylizers
            </div>
            <div className="rainbow z-10 text-6xl min-h-[5rem]">
              Welcome Stylizers
            </div>
            
            <form 
              onSubmit={(e) => e.preventDefault()}
              className="w-1/2 p-3 flex flex-col items-center justify-center gap-y-8 z-10 min-w-[300px]" 
              action="">
              <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-gray-800 border-gray-600 hover:border-blue-700">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <svg aria-hidden="true" className="w-10 h-10 mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                      </svg>
                      <p className="mb-2 text-sm text-gray-500 dark:text-gray-400"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">MP4 and JPG</p>
                  </div>
                  <input id="dropzone-file" type="file" multiple className="hidden" onChange={onFileUploadChange}/>
              </label>
              <div 
              className="w-full flex justify-between items-center">
                <button 
                  className='bg-black p-2 px-8 rounded-lg hover:bg-gray-900 cursor-pointer disabled:hover:bg-black disabled:cursor-default'
                  onClick={onSubmit}
                  disabled={files.length === 0}
                >
                  Upload
                </button>
                {
                  imagePaths.length == 2 ?
                  <div className="flex flex-col items-center">
                    <button className="bg-blue-800 p-1 rounded-[5rem] cursor-pointer hover:bg-blue-600" onClick={onTransfer}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="1rem" height="1rem" fill="currentColor" className="bi bi-arrow-repeat" viewBox="0 0 16 16">
                        <path d="M11.534 7h3.932a.25.25 0 0 1 .192.41l-1.966 2.36a.25.25 0 0 1-.384 0l-1.966-2.36a.25.25 0 0 1 .192-.41zm-11 2h3.932a.25.25 0 0 0 .192-.41L2.692 6.23a.25.25 0 0 0-.384 0L.342 8.59A.25.25 0 0 0 .534 9z"/>
                        <path fillRule="evenodd" d="M8 3c-1.552 0-2.94.707-3.857 1.818a.5.5 0 1 1-.771-.636A6.002 6.002 0 0 1 13.917 7H12.9A5.002 5.002 0 0 0 8 3zM3.1 9a5.002 5.002 0 0 0 8.757 2.182.5.5 0 1 1 .771.636A6.002 6.002 0 0 1 2.083 9H3.1z"/>
                      </svg>
                    </button> 
                    <p>
                      Transfer
                    </p>
                  </div>:
                  <p className="align-middle">
                    <strong>{files.length} / 2</strong> files
                  </p>
                }
                <button
                  className="bg-red-950 p-2 px-8 rounded-lg hover:bg-red-900 cursor-pointer disabled:hover:bg-red-950 disabled:cursor-default"
                  onClick={onCancelFile}
                  disabled={files.length === 0}
                >
                  Cancel
                </button>
              </div>
              <div
              className="w-full flex justify-between max-h-[20vh] overflow-hidden"
              >
                {thumbnailUrl && 
                <img alt="thumbnail" src={thumbnailUrl} className={`max-h-[100%] max-w-[40%] rounded-lg border-4 ${files[0].uploaded ? 'border-green-500' : 'border-blue-600'}`}/>
                }
                {
                  previewUrls.map((prev, index) => {
                    return (
                      <img
                        className={`max-h-[100%] max-w-[40%] border-4 rounded-lg ${files[index + (thumbnailUrl ? 1 : 0)].uploaded ? 'border-green-500' : 'border-blue-600'}`}
                        alt="file uploader preview"
                        src={prev}
                        key={index}
                      />
                    )
                  })
                }
              </div>
            </form>
          </div>
        </>
      }
    </div>
  )
}
