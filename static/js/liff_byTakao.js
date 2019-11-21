window.onload = function (e) {
    // init で初期化。基本情報を取得。
    // https://developers.line.me/ja/reference/liff/#initialize-liff-app
        liff.init(function (data){
            document.getElementById("idChecker").addEventListener('click',function(){
                getProfile();
            });
            document.getElementById("closeButton").addEventListener('click',function(){
                liff.closeWindow();
            });
            document.getElementById("sendButton").addEventListener('click',function(){
                userId = document.getElementById("userIdField").textContent;
                errorP1 = document.getElementById("errorP1");
                errorP2 = document.getElementById("errorP2");
                zipcode = document.getElementById("zipcode").value;
                address = document.getElementById("streetAddress").value;

                if(zipcode.length!=7 || address=="" || streetAddress==""){
                    errorP1.textContent = "入力値が誤ってませんか？";
                    if(userId=="")
                        errorP2.textContent = "ユーザーIDの送信が承諾されてません！";
                }else if(userId==""){
                    errorP1.textContent= "";
                    errorP2.textContent = "ユーザーIDの送信が承諾されてません！";
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


