import os
import email
import pdfkit
import email.utils
import email.header
import re
import argparse

options = {"quiet": True, "load-error-handling": "skip", "encoding": "UTF-8"}


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Convert EML files to PDF")
    parser.add_argument("input_dir", help="Directory containing EML files")
    parser.add_argument("output_dir", help="Directory for PDF output")
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Process all .eml files in input directory
    for filename in os.listdir(args.input_dir):
        if not filename.lower().endswith(".eml"):
            continue

        eml_path = os.path.join(args.input_dir, filename)

        # Open and parse the .eml file
        with open(eml_path, "r") as f:
            msg = email.message_from_file(f)

        # Extract HTML content from the email
        html_content = None

        # Format email header
        from_addr = msg.get("from", "No sender")
        to_addr = msg.get("to", "No recipient")
        date = email.utils.parsedate_to_datetime(msg.get("date", ""))
        formatted_date = date.strftime("%Y-%m-%d, %H:%M") if date else "No date"

        # Decode subject if it's encoded
        subject = msg.get("subject", "No subject")
        if subject:
            try:
                decoded_subject = email.header.decode_header(subject)[0]
                subject = (
                    decoded_subject[0].decode("utf-8")
                    if isinstance(decoded_subject[0], bytes)
                    else decoded_subject[0]
                )
            except Exception as e:
                print(f"Failed to decode subject for {filename}: {str(e)}")

        email_header = f"""
        <pre style="font-family: monospace; margin-bottom: 20px;">
from:    {from_addr}
to:      {to_addr}
date:    {formatted_date}
subject: {subject}
        </pre>
        <hr>
        """

        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                # Try multiple encodings if UTF-8 fails
                if isinstance(payload, bytes):
                    for encoding in ["utf-8", "latin1", "iso-8859-1", "cp1252"]:
                        try:
                            html_content = payload.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:  # If no encoding worked
                        print(
                            f"Failed to decode {filename} with common encodings. Skipping..."
                        )
                        continue
                else:
                    html_content = payload
                break

        # Convert to PDF if HTML content is found
        if html_content:
            # Add UTF-8 meta tag and email header if not present
            if isinstance(html_content, str):
                html_content = f"""
                    <meta charset="UTF-8">
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
                    {email_header}
                    {html_content}
                """

            # Format date for filename prefix
            file_date = date.strftime("%Y-%m-%d") if date else "nodate"

            # Create sanitized subject for filename
            safe_subject = re.sub(r'[<>:"/\\|?*]', "", subject)  # Remove illegal chars
            safe_subject = safe_subject.replace(
                " ", "_"
            )  # Replace spaces with underscores

            # Create base output filename
            base_filename = f"{file_date}-{safe_subject}.pdf"
            output_path = os.path.join(args.output_dir, base_filename)

            # Add number suffix if file exists
            counter = 1
            while os.path.exists(output_path):
                base_filename = f"{file_date}-{safe_subject}_{counter}.pdf"
                output_path = os.path.join(args.output_dir, base_filename)
                counter += 1

            # Convert to PDF
            try:
                pdfkit.from_string(html_content, output_path, options=options)
                print(f"Converted {filename} to PDF successfully.")
            except OSError as e:
                print(f"Failed to convert {filename}: {str(e)}")
                # Optionally, try again with images disabled
                try:
                    options["load-error-handling"] = "ignore"
                    options["no-images"] = True
                    pdfkit.from_string(html_content, output_path, options=options)
                    print(f"Converted {filename} to PDF successfully (without images).")
                except Exception as e2:
                    print(f"Second attempt failed for {filename}: {str(e2)}")
                    continue
        else:
            print(f"No HTML content found in {filename}. Skipping...")

    print("All .eml files processed.")


if __name__ == "__main__":
    main()
