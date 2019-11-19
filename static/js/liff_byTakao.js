window.onload = function (e) {
    // init で初期化。基本情報を取得。
    // https://developers.line.me/ja/reference/liff/#initialize-liff-app
        liff.init(function (data){
            document.getElementById("displayButton").addEventListener('click',function(){
                getProfile();
            });
            document.getElementById("closeButton").addEventListener('click',function(){
                liff.closeWindow();
            });
            document.getElementById("sendButton").addEventListener('click',function(){
                userId = document.getElementById("userIdField").textContent
                errorP = document.getElementById("errorP")
                zipcode = document.getElementById("zipcode").value
                address = document.getElementById("streetAddress").value

                if(userId!="" | zipcode.length==7 || address!=""){
                    liff.closeWindow();
                }else{
                    errorP.textContent = "ちゃんとボタンは押しましたか？\n入力値が誤ってませんか？";
                }
            });
        });
    };

    function getProfile(){
        liff.getProfile().then(function (profile){
            //useridを渡す。
            document.getElementById('userIdField').textContent=profile.userId;
            document.getElementById('userId').value=profile.userId;
        });
    };


