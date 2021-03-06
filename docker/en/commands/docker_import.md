



[docker import](https://docs.docker.com/engine/reference/commandline/import/)

> Import to docker from a local archive.
>
> ```
> $ docker import /path/to/exampleimage.tgz
> ```



[docker image를 tar 파일로 저장 (export / import / save / load)](https://www.leafcats.com/240)

> (중요) export - import 와 save - load의 차이
>
> docker export의 경우 컨테이너를 동작하는데 필요한 모든 파일이 압충된다. 즉, tar파일에 컨테이너의 루트 파일시스템 전체가 들어있는 것이다. 반면에 docker save는 레이어 구조까지 포함한 형태로 압축이 된다.
>
> 즉, 기반이 되는 이미지가 같더라도 export와 save는 압축되는 파일 구조와 디렉터리가 다르다.
>
> 결론은 export를 통해 생성한 tar 파일은 import로, save로 생성한 파일은 load로 이미지화 해야 한다.