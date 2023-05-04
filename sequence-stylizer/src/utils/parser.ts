import formidable from "formidable"
import { mkdir, stat } from "fs/promises";
import type { NextApiRequest } from "next";
import mime from "mime";
import { join } from "path";
import * as dateFn from "date-fns";

export const FormidableError = formidable.errors.FormidableError;

export const parseForm = async (
  req: NextApiRequest
): Promise<{ fields: formidable.Fields; files: formidable.Files }> => {
  return new Promise(async (resolve, reject) => {

    let filePaths: string[] = []

    const uploadDir = join(
        process.cwd(),
        `/public/${dateFn.format(Date.now(), "dd-MM-Y")}`
    )
  
    try {
        await stat(uploadDir) // check if directory exists
    } catch (e: any) {
        if (e.code === "ENOENT") {
            await mkdir(uploadDir, { recursive: true }) // makes directory if it does not exist
        } else {
            console.error(e)
            reject(e)
            return
        }
    }

    const form = formidable({
        maxFileSize: 10 * 1024 * 1024 * 1024, // 10gb
        uploadDir,
        multiples: true,
        filename: (_name, _ext, part) => {
          const suffix = `${Date.now()}-${Math.round(Math.random() * 1e9)}`
          // default unknown
          const filename = `${part.name || "unknown"}-${suffix}.${
            mime.getExtension(part.mimetype || "") || "unknown"
          }`
          filePaths.push(filename)
          return filename
        },
        filter: (part) => {
          // only allow files of key media and of type image
          return (
            part.name === "media" && ((part.mimetype?.includes("image") || part.mimetype?.includes("video")) || false)
          )
        },
    })

    form.parse(req, (err, fields, files) => {
        if (err) reject(err)
        else resolve({ fields, files })
    });
  })
}