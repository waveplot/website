
function HelpCtrl($scope, $modal, $http){
    //Placeholder question until the server supports this.
    $scope.openQuestion = function(id) {
        $http.get('/api/question/'+id.toString()).success(function (data) {
            $modal.open({
                templateUrl: '/app/help/question-modal.html',
                controller: QuestionModalController,
                resolve: {
                    question: function () {
                        return data;
                    }
                }
            });
        });
    };

    $http.get('/api/question').success(function (data) {
        $scope.questions = [];
        $.each(data, function(k,v){
            if(v.answered != false){
                $scope.questions.push(v);
            }
        });
    });

}

HelpCtrl.resolve = {
    lang: function($translate, $translatePartialLoader, $q){
        $translatePartialLoader.addPart('help');
        return $translate.refresh();
    }
}
