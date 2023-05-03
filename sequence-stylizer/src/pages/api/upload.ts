import type { NextApiRequest, NextApiResponse } from "next";
import { parseForm, FormidableError } from "@component/utils/parser";
import sharp from "sharp";
import { spawn } from "child_process";


export const config = {
  api: {
    responseLimit: false,
    bodyParser: false,
  },
}

export type ResponseType = {
    data: {
      url: string | string[];
    } | null;
    error: string | null;
  }

  
  export default async function handler (
  req: NextApiRequest,
  res: NextApiResponse<ResponseType>
  ) {
  console.log("request received");
  
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    res.status(405).json({
      data: null,
      error: "Method Not Allowed",
    });
    return;
  }
  
  try {
    const { fields, files } = await parseForm(req)
    
    const file = files.media;
    const url = Array.isArray(file) ? file.map((f) => f.filepath) : [file.filepath];
    
    // const imagePath = url[0]
    // console.log('before process')
    // const pythonProcess = spawn('py', ['src/utils/script.py', imagePath])

    // console.log('mid process')
    
    // pythonProcess.stdout.on('data', (data) => {
    //   console.log(`stdout: ${data}`);
    // })
    
    // pythonProcess.stderr.on('data', (data) => {
    //   console.error(`stderr: ${data}`);
    // })
    
    // pythonProcess.on('close', (code) => {
    //   console.log(`child process exited with code ${code}`);
    // })
    
    // console.log('after process')

    // sharp(imagePath)
    //   .metadata()
    //   .then(metadata => {
    //     console.log(`Image dimensions: ${metadata.width}x${metadata.height}`);
    //   })
    //   .catch(err => {
    //     console.error(`Error reading image metadata: ${err.message}`);
    //   });
  
    res.status(200).json({
      data: {
        url: url,
      },
      error: null,
    });
  } catch (e) {
    if (e instanceof FormidableError) {
      res.status(400).json({ data: null, error: e.message });
    } else {
      console.error(e);
      res.status(500).json({ data: null, error: "Internal Server Error" });
    }
  }

}
