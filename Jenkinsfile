pipeline {
    agent { label 'hsio' }
    stages {
        stage('run test') {
            steps {
                echo 'start pipeline'
                bat '''
                echo 'hello world'
                set curr_dir=%cd%
                xcopy /e /v %cd% C:\\Jenkins\\%BUILD_ID%\\
                C:\\Python38\\python.exe C:\\Jenkins\\%BUILD_ID%\\src\\hsio\\upi\\functional\\upi_linkwidth.py
                '''
            }
        }
    }
    post {
        always {
            bat "rmdir /S /Q C:\\Jenkins\\%BUILD_ID%\\"
        }
    }
}
