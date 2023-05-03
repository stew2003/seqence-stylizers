import type { NextApiRequest, NextApiResponse } from "next"
import { parseForm, FormidableError } from "@component/utils/parser"

export const config = {
  api: {
    responseLimit: false,
    bodyParser: false,
  },
}

export type UploadResponseType = {
    data: {
      url: string[]
    } | null
    error: string | null
  }

  
export default async function handler (
  req: NextApiRequest,
  res: NextApiResponse<UploadResponseType>
  ) {
  console.log("upload request received")
  
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST")
    res.status(405).json({
      data: null,
      error: "Method Not Allowed",
    })
    return
  }
  
  try {
    const { fields, files } = await parseForm(req)
    
    const file = files.media
    const url = Array.isArray(file) ? file.map((f) => f.filepath) : [file.filepath]

    res.status(200).json({
      data: {
        url: url,
      },
      error: null,
    })
  } catch (e) {
    if (e instanceof FormidableError) {
      res.status(400).json({ data: null, error: e.message })
    } else {
      console.error(e)
      res.status(500).json({ data: null, error: "Internal Server Error" })
    }
  }

}
