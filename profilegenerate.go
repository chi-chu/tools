package main

import (
    "fmt"
    "os"
    "runtime/pprof"
    "time"
)

//go tool pprof -svg  .\   D:\GoWork\src\cpu.pprof.201906181737 > cpu.svg

//go tool pprof -alloc_space/-inuse_space  D:\GoWork\src\mem.pprof.201906181737 > mem.svg


//default profile will create at gopath   depend on your setting path
func main(){
    suffix := time.Now().Format("200601021504")
    fp, err := os.Create(fmt.Sprintf("mem.pprof.%v", suffix))
    defer fp.Close()
    if err != nil {
        return
    }
    if err := pprof.WriteHeapProfile(fp); err != nil {
        return
    }

    fp2, err := os.Create(fmt.Sprintf("cpu.pprof.%v", suffix))
    defer fp2.Close()
    if err != nil {
        return
    }
    if err := pprof.StartCPUProfile(fp2); err != nil {
        return
    }
    defer pprof.StopCPUProfile()

    testfmt()
    makesl()
}

func testfmt(){
    for i:=1;i<100;i++{
        fmt.Println("hello world")
    }
    addmap()
}

func makesl(){
    list := []int{1}
    c := 1
    for i := 0; i < 10000000; i++ {
        c = i + 1 + 2 + 3 + 4 - 5
        list = append(list, c)
    }
    fmt.Println(c)
    fmt.Println(list[0])
}

func addmap(){
    mmp := make(map[int]string)
    for i:=0;i<10000;i++{
        mmp[i] = "safhafgsadfasdfh"
    }
}