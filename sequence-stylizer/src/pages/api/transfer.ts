import { NextApiRequest, NextApiResponse } from "next"
import { spawn } from "child_process"
import { url } from "inspector"

export const config = {
    api: {
        responseLimit: false,
    },
}

export type TransferResponseType = {
    data: {
      status: string | null
      message: string | null
    } | null
    error: string | null
}

let complete = ""
let error: string | null = null

export default async function handler (
    req: NextApiRequest,
    res: NextApiResponse<TransferResponseType>
) {
    if (req.method !== "POST" && req.method !== "GET") {
        console.log("illegal transfer request received")
        res.setHeader("Allow", "POST, GET")
        res.status(405).json({
        data: null,
        error: "Method Not Allowed",
    })
    return
}

if (req.method === "POST") {
        console.log("post transfer request received")
        const mediaPaths = JSON.parse(req.body)
        try {
            console.log('before process')
            const scriptPath = 'src/utils/scripts/main.py'
            const suffix = mediaPaths[0].slice(-3)
            
            let flag = '--image'
            if (suffix === 'mp4') flag = '--video'

            const activateProcess = spawn(`conda run -n cs1430 python ${scriptPath} ${flag} ${mediaPaths[0].replaceAll(' ', '\\ ')} --style ${mediaPaths[1].replaceAll(' ', '\\ ')}`, { shell: true, stdio: 'pipe' })
            activateProcess.stdout.pipe(process.stdout);
    
            activateProcess.stdout.on('data', (data) => {
                console.log('stdout: ' + data.toString().trim())
            })
              
            activateProcess.stderr.on('data', (data) => {
                console.log('stderr: ' + data.toString().trim())
                error = data.toString().trim()
            })
    
            activateProcess.on('close', (code) => {
                console.log(`child process exited with code ${code}`)
                if (code === 0) {
                    complete = flag
                }
            })
            
            res.status(200).json({
                data: {
                    status: null,
                    message: "script is running"
                },
                error: null,
            })
        } catch (e) {
            console.error(e)
            res.status(500).json({ data: null, error: "Internal Server Error" })
        }
    } else {
        console.log('get transfer request received')
        res.status(200).json({
            data: {
                status: complete,
                message: null
            },
            error: error,
        })
        return
    }

}
