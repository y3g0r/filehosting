# filehosting
python main/hosting_app.py

## Instructions

- Use uri to pass in target of operation.
- If uri is finished with '/' you are targeting folder operations ('/', '/some/deep/dir/'), otherwise operation will target files ('/afile', '/some/deep/file'). Exception for DELETE method ('/file_or_folder' with DELETE method will delete whatever is actually stored in this path)
- All operation are reflected in DB

### GET

Use GET HTTP method to download file or get filesystem tree.

- 200 - Success
- 203 - The server is successfully fulfilling a range request
- 403 - Don't have permission to perform operation on provided path
- 404 - File doesn't exist

### PUT

Use PUT HTTP method to upload file or create directory

- 200 - Success
- 403 - Don't have permission to perform operation on provided path
- 409 - Conflict with existing file tree (Already exists or one of the components in path is not a dir)

### DELETE

Use DELETE HTTP method to delete file or directory tree

- 200 - Success
- 403 - Don't have permission to perform operation on provided path
- 404 - File or folder does not exists


## Example of usage

##### Get file tree starting from root
```
$ curl -i -X GET localhost:8888/
```

```HTTP
HTTP/1.1 404 Not Found
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 11:06:47 GMT
Content-Length: 59
Content-Type: application/json; charset=UTF-8

{
	"errors": [{
		"error_msg": "Not Found",
		"error_code": 404
	}]
}
```

##### Create root folder
```
$ curl -i -X PUT localhost:8888/
```

```HTTP
HTTP/1.1 200 OK
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 11:08:10 GMT
Content-Length: 119
Content-Type: application/json; charset=UTF-8

{
	"path": "/",
	"bytes": 4096,
	"size": "4.0KiB",
	"modified": "Fri, 01 Jul 2016 14:08:10",
	"is_dir": true,
	"children": []
}
```
In response of method PUT you get updated/created filesystem tree or error message


##### Create nested folder
```
$ curl -i -X PUT localhost:8888/learn/coursera/funprog/
```

```HTTP
HTTP/1.1 200 OK
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 11:41:40 GMT
Content-Length: 511
Content-Type: application/json; charset=UTF-8

{
	"path": "/",
	"bytes": 4096,
	"size": "4.0KiB",
	"modified": "Fri, 01 Jul 2016 14:41:40",
	"is_dir": true,
	"children": {
		"path": "/learn",
		"bytes": 4096,
		"size": "4.0KiB",
		"modified": "Fri, 01 Jul 2016 14:41:40",
		"is_dir": true,
		"children": {
			"path": "/learn/coursera",
			"bytes": 4096,
			"size": "4.0KiB",
			"modified": "Fri, 01 Jul 2016 14:41:40",
			"is_dir": true,
			"children": {
				"path": "/learn/coursera/funprog",
				"bytes": 4096,
				"size": "4.0KiB",
				"modified": "Fri, 01 Jul 2016 14:41:40",
				"is_dir": true,
				"children": []
			}
		}
	}
}
```

##### Get non existing file
```
$ curl -i -X GET localhost:8888/learn/coursera/funprog/lec_2.2_currying.mp4
```
```HTTP
HTTP/1.1 404 Not Found
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 11:46:01 GMT
Content-Length: 59
Content-Type: application/json; charset=UTF-8

{
	"errors": [{
		"error_msg": "Not Found",
		"error_code": 404
	}]
}
```

##### Upload file
```
$ curl -i -X PUT --data-binary "@lec_2.2_currying.mp4" localhost:8888/learn/coursera/funprog/lec_2.2_currying.mp4
```
```HTTP
HTTP/1.1 100 (Continue)

HTTP/1.1 200 OK
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 11:48:40 GMT
Content-Length: 291
Content-Type: application/json; charset=UTF-8

{
	"path": "/learn/coursera/funprog",
	"bytes": 4096,
	"size": "4.0KiB",
	"modified": "Fri, 01 Jul 2016 14:48:40",
	"is_dir": true,
	"children": {
		"path": "/learn/coursera/funprog/lec_2.2_currying.mp4",
		"bytes": 10606200,
		"size": "10.1MiB",
		"modified": "Fri, 01 Jul 2016 14:48:40",
		"is_dir": false
	}
}
```

##### Upload file to non existing folder
```
$ curl -i -X GET localhost:8888/not/exists/
```
```HTTP
HTTP/1.1 404 Not Found
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 11:50:54 GMT
Content-Length: 59
Content-Type: application/json; charset=UTF-8

{
	"errors": [{
		"error_msg": "Not Found",
		"error_code": 404
	}]
}
```
```
$ curl -i -X PUT --data-binary "@lec_2.2_currying.mp4" localhost:8888/not/exists/lec_2.2_currying.mp4
```
```HTTP
HTTP/1.1 100 (Continue)

HTTP/1.1 200 OK
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 11:53:51 GMT
Content-Length: 1089
Content-Type: application/json; charset=UTF-8

{
	"path": "/",
	"bytes": 4096,
	"size": "4.0KiB",
	"modified": "Fri, 01 Jul 2016 14:56:31",
	"is_dir": true,
	"children": {
		"path": "/not",
		"bytes": 4096,
		"size": "4.0KiB",
		"modified": "Fri, 01 Jul 2016 14:56:31",
		"is_dir": true,
		"children": {
			"path": "/not/exists",
			"bytes": 4096,
			"size": "4.0KiB",
			"modified": "Fri, 01 Jul 2016 14:56:31",
			"is_dir": true,
			"children": {
				"path": "/not/exists/lec_2.2_currying.mp4",
				"bytes": 10606200,
				"size": "10.1MiB",
				"modified": "Fri, 01 Jul 2016 14:56:31",
				"is_dir": false
			}
		}
	}
}
```
In response all updated or created nodes are included



##### Upload another file
```
$ curl -X PUT localhost:8888/simple.json -d "{"hello": "World"}"

{
	"path": "/",
	"bytes": 4096,
	"size": "4.0KiB",
	"modified": "Fri, 01 Jul 2016 15:11:41",
	"is_dir": true,
	"children": {
		"path": "/simple.json",
		"bytes": 14,
		"size": "14.0B",
		"modified": "Fri, 01 Jul 2016 15:11:41",
		"is_dir": false
	}
}
```

##### Get file
```
$ curl -X GET localhost:8888/simple.json
```
```HTTP
HTTP/1.1 200 OK
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 12:13:30 GMT
Etag: "62c744bc1a969f27f4dbe9549039cfbc"
Last-Modified: Fri, 01 Jul 2016 12:11:41 GMT
Content-Type: application/json
Accept-Ranges: bytes
Content-Length: 14

{hello: World}
```

##### Get file partial
```
$ curl -i -X GET -H "Range:bytes=0-5" localhost:8888/simple.json
```
```HTTP
HTTP/1.1 206 Partial Content
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 12:16:20 GMT
Content-Range: bytes 0-5/14
Etag: "62c744bc1a969f27f4dbe9549039cfbc"
Last-Modified: Fri, 01 Jul 2016 12:11:41 GMT
Content-Type: application/json
Accept-Ranges: bytes
Content-Length: 6

{hello
```

##### Delete file
```
$ curl -i -X DELETE localhost:8888/simple.json
```
```HTTP
HTTP/1.1 200 OK
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 12:18:13 GMT
Content-Length: 0
Content-Type: text/html; charset=UTF-8

```

##### Create empty file
```
$ curl -i -X PUT localhost:8888/empty.file
```
```HTTP
HTTP/1.1 200 OK
Server: TornadoServer/4.3
Date: Fri, 01 Jul 2016 12:22:20 GMT
Content-Length: 226
Content-Type: application/json; charset=UTF-8

{"path": "/", "bytes": 4096, "size": "4.0KiB", "modified": "Fri, 01 Jul 2016 15:22:20", "is_dir": true, "children": {"path": "/empty.file", "bytes": 0, "size": "0.0B", "modified": "Fri, 01 Jul 2016 15:22:20", "is_dir": false}}%
```

##### Create folder with conflict path
```
$ curl -i -X PUT localhost:8888/empty.file/somedir/
```
```HTTP
HTTP/1.1 409 Conflict
Server: TornadoServer/4.3
Content-Length: 58
Date: Fri, 01 Jul 2016 12:26:37 GMT
Content-Type: application/json; charset=UTF-8

{"errors": [{"error_code": 409, "error_msg": "Conflict"}]}
```

##### Get the whole picture
```
$ curl -X GET localhost:8888/

{
	"path": "/",
	"bytes": 4096,
	"size": "4.0KiB",
	"modified": "Fri, 01 Jul 2016 15:30:07",
	"is_dir": true,
	"children": [{
		"path": "/not",
		"bytes": 4096,
		"size": "4.0KiB",
		"modified": "Fri, 01 Jul 2016 14:59:19",
		"is_dir": true,
		"children": [{
			"path": "/not/exists",
			"bytes": 4096,
			"size": "4.0KiB",
			"modified": "Fri, 01 Jul 2016 14:59:19",
			"is_dir": true,
			"children": [{
				"path": "/not/exists/lec_2.2_currying.mp4",
				"bytes": 10606200,
				"size": "10.1MiB",
				"modified": "Fri, 01 Jul 2016 14:59:19",
				"is_dir": false
			}]
		}]
	}, {
		"path": "/learn",
		"bytes": 4096,
		"size": "4.0KiB",
		"modified": "Fri, 01 Jul 2016 14:58:41",
		"is_dir": true,
		"children": [{
			"path": "/learn/coursera",
			"bytes": 4096,
			"size": "4.0KiB",
			"modified": "Fri, 01 Jul 2016 14:58:41",
			"is_dir": true,
			"children": [{
				"path": "/learn/coursera/funprog",
				"bytes": 4096,
				"size": "4.0KiB",
				"modified": "Fri, 01 Jul 2016 14:58:41",
				"is_dir": true,
				"children": [{
					"path": "/learn/coursera/funprog/lec_2.2_currying.mp4",
					"bytes": 10606200,
					"size": "10.1MiB",
					"modified": "Fri, 01 Jul 2016 14:58:41",
					"is_dir": false
				}]
			}]
		}]
	}]
}
```
##### Delete folder
```
$ curl -i -X DELETE localhost:8888/learn/coursera/funprog

HTTP/1.1 200 OK
Server: TornadoServer/4.3
Content-Length: 0
Date: Fri, 01 Jul 2016 12:36:36 GMT
Content-Type: text/html; charset=UTF-8

```
```
$ curl -X GET localhost:8888/learn/

{
	"path": "/learn",
	"bytes": 4096,
	"size": "4.0KiB",
	"modified": "Fri, 01 Jul 2016 14:58:41",
	"is_dir": true,
	"children": [{
		"path": "/learn/coursera",
		"bytes": 4096,
		"size": "4.0KiB",
		"modified": "Fri, 01 Jul 2016 15:36:36",
		"is_dir": true,
		"children": []
	}]
}
```

[1]: https://github.com/jkbrzt/httpie