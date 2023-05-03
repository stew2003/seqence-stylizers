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
      url: string | null
      message: string | null
    } | null
    error: string | null
}

let path = ""

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
        const imagePaths = JSON.parse(req.body)
        try {
            console.log('before process')
            const activateCommand = 'conda activate cs1430'
            const scriptPath = 'src/utils/script.py'
    
            const activateProcess = spawn(activateCommand, [], { shell: true })
            activateProcess.stdout.on('data', (data) => {
                console.log('stdout: ' + data)
            })
              
            activateProcess.stderr.on('data', (data) => {
                console.log('stderr: ' + data)
            })
    
            let url = ""
            activateProcess.on('close', (code) => {
                console.log(`child process exited with code ${code}`)
                if (code === 0) {
                    const pythonProcess = spawn('py', [scriptPath, imagePaths[0]])
              
                    pythonProcess.stdout.on('data', (data) => {
                        url = data.toString().trim()
                        console.log('stdout: ' + data)
                        console.log(url)
                    })
              
                    pythonProcess.stderr.on('data', (data) => {
                        console.error('stderr: ' + data)
                    })
              
                    pythonProcess.on('close', (code) => {
                        console.log(`child process exited with code ${code}`)
                        path = url
                    })
                } else {
                    console.error(`Failed to activate Conda environment`)
                }
            })
            
            res.status(200).json({
                data: {
                    url: null,
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
                url: path,
                message: null
            },
            error: null,
        })
        return
    }

}
